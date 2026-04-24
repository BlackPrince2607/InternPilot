from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.services.behavior_ranker import BehaviorProfile, compute_behavior_score
from app.services.domain_detector import detect_domain, domain_similarity
from app.services.job_skill_extractor import JobSkillProfile, extract_job_skill_profile
from app.services.skill_normalizer import (
    categorize_skill,
    enrich_resume_skills,
    expand_with_related,
    extract_terms_from_text,
    flatten_skills,
    get_related_skills,
    normalize_skill,
    normalize_terms,
)
from app.utils.matching import location_matches, role_matches_title


@dataclass(slots=True)
class UserProfile:
    domain: str
    base_skills: set[str]
    core_skills: set[str]
    project_skills: set[str]
    experience_skills: set[str]
    skill_depth: dict[str, float]
    preferred_roles: list[str]
    preferred_locations: list[str]
    remote_ok: bool
    project_text: str
    experience_text: str
    resume_text: str


@dataclass(slots=True)
class MatchResult:
    accepted: bool
    final_score: float = 0.0
    skill_match_score: float = 0.0
    project_relevance_score: float = 0.0
    experience_depth_score: float = 0.0
    semantic_similarity_score: float = 0.0
    role_match_score: float = 0.0
    location_match_score: float = 0.0
    behavior_score: float = 0.5
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    skill_gaps: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    filter_reason: str | None = None
    domain: str = "general"
    confidence_level: str = "Low"
    selection_probability: float = 0.0


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _stringify_items(items: list[Any]) -> str:
    parts: list[str] = []
    for item in items:
        if isinstance(item, dict):
            parts.extend(str(value) for value in item.values() if value)
        elif item:
            parts.append(str(item))
    return "\n".join(parts)


def _clean_skill_values(skills: list[str] | set[str]) -> set[str]:
    cleaned: set[str] = set()
    for skill in skills:
        normalized = normalize_skill(skill)
        if not normalized or normalized.isdigit() or len(normalized) <= 1:
            continue
        cleaned.add(normalized)
    return cleaned


def _ordered_clean_skills(skills: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in skills:
        normalized = normalize_skill(raw)
        if not normalized or normalized in seen or normalized.isdigit() or len(normalized) <= 1:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _build_skill_depth(extracted_data: dict[str, Any]) -> tuple[set[str], set[str], dict[str, float]]:
    base_skills = _clean_skill_values(flatten_skills(extracted_data.get("skills")))
    project_counter: Counter[str] = Counter()
    experience_counter: Counter[str] = Counter()

    for project in extracted_data.get("projects") or []:
        project_text = " ".join(
            str(value)
            for value in [
                project.get("name"),
                project.get("description"),
                " ".join(project.get("technologies") or []),
                " ".join(project.get("highlights") or []),
            ]
            if value
        )
        for token in _clean_skill_values(extract_terms_from_text(project_text)):
            project_counter[token] += 1

    for experience in extracted_data.get("experience") or []:
        experience_text = " ".join(
            str(value)
            for value in [
                experience.get("company"),
                experience.get("role"),
                " ".join(experience.get("highlights") or []),
            ]
            if value
        )
        for token in _clean_skill_values(extract_terms_from_text(experience_text)):
            experience_counter[token] += 1

    depth: dict[str, float] = {}
    for skill in set(base_skills) | set(project_counter.keys()) | set(experience_counter.keys()):
        depth[skill] = (
            1.0 * (1 if skill in base_skills else 0)
            + 1.2 * project_counter.get(skill, 0)
            + 1.8 * experience_counter.get(skill, 0)
        )

    return set(project_counter.keys()), set(experience_counter.keys()), depth


def build_user_profile(extracted_data: dict[str, Any], preferences: dict[str, Any] | None) -> UserProfile:
    preferences = preferences or {}
    preferred_roles = normalize_terms(preferences.get("preferred_roles"))
    preferred_locations = normalize_terms(preferences.get("preferred_locations"))
    remote_ok = bool(preferences.get("remote_ok"))

    project_skills, experience_skills, skill_depth = _build_skill_depth(extracted_data)
    ordered_resume_skills = _ordered_clean_skills(flatten_skills(extracted_data.get("skills")))
    core_skills = set(ordered_resume_skills[:8])
    base_skills = enrich_resume_skills(set(ordered_resume_skills))
    project_skills = enrich_resume_skills(project_skills)
    experience_skills = enrich_resume_skills(experience_skills)
    project_text = _stringify_items(extracted_data.get("projects") or [])
    experience_text = _stringify_items(extracted_data.get("experience") or [])
    resume_text = "\n".join(
        part
        for part in [
            extracted_data.get("college") or "",
            " ".join(sorted(base_skills)),
            project_text,
            experience_text,
        ]
        if part
    )
    domain, _ = detect_domain(
        resume_text,
        skills=list(base_skills | project_skills | experience_skills),
    )

    return UserProfile(
        domain=domain,
        base_skills=base_skills,
        core_skills=core_skills,
        project_skills=project_skills,
        experience_skills=experience_skills,
        skill_depth=skill_depth,
        preferred_roles=preferred_roles,
        preferred_locations=preferred_locations,
        remote_ok=remote_ok,
        project_text=project_text,
        experience_text=experience_text,
        resume_text=resume_text,
    )


class MatchEngine:
    min_skill_overlap = 0.13
    min_semantic_similarity = 0.27
    minimum_score = 0.42

    def __init__(self, user_profile: UserProfile, behavior_profile: BehaviorProfile | None = None) -> None:
        self.user = user_profile
        self.behavior = behavior_profile or BehaviorProfile({}, {}, {})
        self.user_skill_space = _clean_skill_values(
            self.user.base_skills | self.user.project_skills | self.user.experience_skills
        )
        self.expanded_user_skills = expand_with_related(self.user_skill_space)
        self._skill_strength_cache: dict[str, float] = {}

    def evaluate_job(self, job: dict[str, Any], semantic_similarity_score: float) -> MatchResult:
        job_profile = extract_job_skill_profile(job)
        title = str(job.get("title") or "")
        location = str(job.get("location") or "")
        domain_score = domain_similarity(self.user.domain, job_profile.domain)
        if domain_score <= 0.10:
            return MatchResult(accepted=False, filter_reason="domain_mismatch", domain=job_profile.domain)

        relevant_job_skills = _clean_skill_values(
            set(job_profile.required_skills or job_profile.critical_skills or job_profile.weighted_keywords)
        )
        if not relevant_job_skills:
            relevant_job_skills = _clean_skill_values(set(job_profile.weighted_keywords.keys()))
        if not relevant_job_skills:
            return MatchResult(accepted=False, filter_reason="missing_job_skills", domain=job_profile.domain)

        skill_overlap, matched_skills = self._weighted_skill_match(job_profile, relevant_job_skills)
        if skill_overlap < self.min_skill_overlap:
            return MatchResult(accepted=False, filter_reason="low_skill_overlap", domain=job_profile.domain)

        if semantic_similarity_score < self.min_semantic_similarity:
            return MatchResult(accepted=False, filter_reason="low_semantic_similarity", domain=job_profile.domain)

        role_match_score = self._role_match_score(title)
        if self.user.preferred_roles and role_match_score < 0.30:
            return MatchResult(accepted=False, filter_reason="role_mismatch", domain=job_profile.domain)

        location_match_score = self._location_match_score(location)
        if (
            not self.user.remote_ok
            and self.user.preferred_locations
            and location_match_score <= 0.0
            and semantic_similarity_score < 0.40
            and skill_overlap < 0.24
        ):
            return MatchResult(accepted=False, filter_reason="location_mismatch", domain=job_profile.domain)

        preference_score = _clip01(0.65 * role_match_score + 0.35 * location_match_score)

        project_relevance = self._project_relevance(job_profile)
        experience_depth = self._experience_depth(job_profile)
        behavior_score = compute_behavior_score(self.behavior, job_profile)

        final_score = (
            0.50 * skill_overlap
            + 0.30 * semantic_similarity_score
            + 0.20 * preference_score
        )

        penalties: list[str] = []
        missing_critical = [skill for skill in job_profile.critical_skills if skill not in matched_skills]
        if domain_score < 0.45:
            final_score *= 0.85
            penalties.append("Partial domain mismatch")
        if skill_overlap < 0.22:
            final_score *= 0.85
            penalties.append("Low core skill overlap")
        if len(missing_critical) > 3:
            final_score *= 0.75
            penalties.append("Missing multiple critical skills")
        if behavior_score > 0.6:
            final_score *= 1.08
            penalties.append("Behavior boost from prior interest")
        elif behavior_score < 0.4:
            final_score *= 0.92
            penalties.append("Behavior penalty from prior skips")

        final_score = _clip01(final_score)
        missing_skills = _clean_skill_values(relevant_job_skills - matched_skills)
        reasons = self._build_reasons(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            role_match_score=role_match_score,
            location_match_score=location_match_score,
            preference_score=preference_score,
            project_relevance=project_relevance,
            experience_depth=experience_depth,
            semantic_similarity_score=semantic_similarity_score,
            skill_overlap=skill_overlap,
            job_domain=job_profile.domain,
        )

        if final_score < self.minimum_score:
            return MatchResult(
                accepted=False,
                final_score=final_score,
                skill_match_score=skill_overlap,
                project_relevance_score=project_relevance,
                experience_depth_score=experience_depth,
                semantic_similarity_score=semantic_similarity_score,
                role_match_score=role_match_score,
                location_match_score=location_match_score,
                behavior_score=behavior_score,
                matched_skills=sorted(matched_skills),
                missing_skills=sorted(missing_skills),
                reasons=reasons,
                penalties=penalties,
                filter_reason="below_threshold",
                domain=job_profile.domain,
                confidence_level=_confidence_level(final_score),
                selection_probability=round(final_score, 4),
            )

        skill_gaps = self._build_skill_gaps(sorted(missing_skills))

        return MatchResult(
            accepted=True,
            final_score=final_score,
            skill_match_score=skill_overlap,
            project_relevance_score=project_relevance,
            experience_depth_score=experience_depth,
            semantic_similarity_score=semantic_similarity_score,
            role_match_score=role_match_score,
            location_match_score=location_match_score,
            behavior_score=behavior_score,
            matched_skills=sorted(matched_skills),
            missing_skills=sorted(missing_skills),
            skill_gaps=skill_gaps,
            reasons=reasons,
            penalties=penalties,
            domain=job_profile.domain,
            confidence_level=_confidence_level(final_score),
            selection_probability=round(final_score, 4),
        )

    def _match_skills(self, job_skills: set[str]) -> set[str]:
        matched: set[str] = set()
        normalized_job_skills = _clean_skill_values(job_skills)
        for skill in normalized_job_skills:
            strength = self._best_skill_match_strength(skill)
            if strength >= 0.55:
                matched.add(skill)
        return matched

    def _best_skill_match_strength(self, job_skill: str) -> float:
        skill = normalize_skill(job_skill)
        if not skill:
            return 0.0

        cached = self._skill_strength_cache.get(skill)
        if cached is not None:
            return cached

        related = get_related_skills(skill)
        if related & self.expanded_user_skills:
            self._skill_strength_cache[skill] = 1.0
            return 1.0

        best = 0.0
        for user_skill in self.user_skill_space:
            if self._skills_partially_match(skill, user_skill):
                best = max(best, 0.65)
        self._skill_strength_cache[skill] = best
        return best

    @staticmethod
    def _skills_partially_match(skill_a: str, skill_b: str) -> bool:
        a = normalize_skill(skill_a)
        b = normalize_skill(skill_b)
        if not a or not b:
            return False
        if a == b:
            return True
        if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
            return True

        tokens_a = set(a.split())
        tokens_b = set(b.split())
        if not tokens_a or not tokens_b:
            return False

        overlap = len(tokens_a & tokens_b)
        return overlap >= max(1, min(len(tokens_a), len(tokens_b)) // 2)

    def _weighted_skill_match(self, job_profile: JobSkillProfile, job_skills: set[str]) -> tuple[float, set[str]]:
        job_skills = _clean_skill_values(job_skills)
        normalized_weights: dict[str, int] = {}
        for raw_skill, raw_weight in job_profile.weighted_keywords.items():
            skill = normalize_skill(raw_skill)
            if not skill:
                continue
            normalized_weights[skill] = normalized_weights.get(skill, 0) + int(raw_weight)

        if not normalized_weights:
            weighted_match = 0.0
            for skill in job_skills:
                weighted_match += self._best_skill_match_strength(skill)
            if len(self.user_skill_space) < 5:
                weighted_match *= 1.15
            overlap = _clip01(weighted_match / max(1, len(job_skills)))
            return overlap, self._match_skills(job_skills)

        total_weight = sum(normalized_weights.values()) or len(normalized_weights) or 1
        matched_skills: set[str] = set()
        matched_weight = 0.0
        for skill, weight in normalized_weights.items():
            strength = self._best_skill_match_strength(skill)
            if strength <= 0.0:
                continue
            core_multiplier = 1.15 if skill in self.user.core_skills else 1.0
            matched_weight += weight * strength * core_multiplier
            if strength >= 0.55:
                matched_skills.add(skill)

        if len(self.user_skill_space) < 5:
            total_weight *= 0.9

        cooccurrence_boost = min(0.12, 0.04 * job_profile.related_skill_groups_hit)
        overlap = _clip01((matched_weight / total_weight) + cooccurrence_boost)
        return overlap, matched_skills

    def _role_match_score(self, title: str) -> float:
        if not self.user.preferred_roles:
            return 0.6
        scores = [1.0 if role_matches_title(role, title) else 0.0 for role in self.user.preferred_roles]
        return max(scores, default=0.0)

    def _location_match_score(self, location: str) -> float:
        if self.user.remote_ok and "remote" in normalize_skill(location):
            return 1.0
        if not self.user.preferred_locations:
            return 0.6 if self.user.remote_ok else 0.4
        if any(location_matches(loc, location) for loc in self.user.preferred_locations):
            return 1.0
        if self.user.remote_ok:
            return 0.4
        return 0.0

    def _project_relevance(self, job_profile: JobSkillProfile) -> float:
        job_skills = set(job_profile.required_skills or job_profile.critical_skills or job_profile.weighted_keywords)
        if not job_skills:
            return 0.0
        matched = self._match_skills(job_skills & self.user.project_skills if self.user.project_skills else job_skills)
        domain_bonus = 0.2 if job_profile.domain == self.user.domain else 0.0
        weighted = sum(job_profile.weighted_keywords.get(skill, 1) for skill in matched)
        total = sum(job_profile.weighted_keywords.get(skill, 1) for skill in job_skills) or 1
        return _clip01((weighted / total) + domain_bonus)

    def _experience_depth(self, job_profile: JobSkillProfile) -> float:
        target_skills = set(job_profile.required_skills or job_profile.critical_skills or job_profile.weighted_keywords)
        if not target_skills:
            return 0.0
        values = [self.user.skill_depth.get(skill, 0.0) for skill in target_skills]
        if not values:
            return 0.0
        max_reasonable_depth = 6.0
        return _clip01(sum(values) / (len(values) * max_reasonable_depth))

    def _build_reasons(
        self,
        matched_skills: set[str],
        missing_skills: set[str],
        role_match_score: float,
        location_match_score: float,
        preference_score: float,
        project_relevance: float,
        experience_depth: float,
        semantic_similarity_score: float,
        skill_overlap: float,
        job_domain: str,
    ) -> list[str]:
        reasons: list[str] = []
        if matched_skills:
            reasons.append(f"Matched skills: {', '.join(sorted(matched_skills)[:5])}")
        if missing_skills:
            reasons.append(f"Missing key skills: {', '.join(sorted(missing_skills)[:4])}")
        if project_relevance >= 0.45:
            reasons.append("Relevant project experience maps to the job stack")
        if experience_depth >= 0.35:
            reasons.append("Resume shows repeated experience with the required skills")
        if semantic_similarity_score >= 0.6:
            reasons.append("High semantic similarity with your resume")
        if role_match_score >= 1.0:
            reasons.append("Matches preferred role closely")
        if location_match_score >= 1.0:
            reasons.append("Location aligns with your preferences")
        if job_domain == self.user.domain and job_domain != "general":
            reasons.append(f"Aligned with your {job_domain} profile")
        reasons.append(
            "Score breakdown: "
            f"skills {round(skill_overlap * 100, 1)}%, "
            f"semantic {round(semantic_similarity_score * 100, 1)}%, "
            f"preference {round(preference_score * 100, 1)}%"
        )
        return reasons[:5] or ["High-signal match after strict relevance filtering"]

    def _build_skill_gaps(self, missing_skills: list[str]) -> list[str]:
        gaps: list[str] = []
        for skill in missing_skills[:4]:
            category = categorize_skill(skill)
            if category == "databases":
                gaps.append(f"Improve {skill} depth for database-heavy roles")
            elif category == "frameworks":
                gaps.append(f"Missing {skill} framework exposure")
            elif category == "tools":
                gaps.append(f"Add hands-on work with {skill}")
            else:
                gaps.append(f"Missing {skill}")
        return gaps


def _confidence_level(score: float) -> str:
    if score >= 0.80:
        return "High"
    if score >= 0.60:
        return "Medium"
    return "Low"
