from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.services.behavior_ranker import BehaviorProfile, compute_behavior_score
from app.services.domain_detector import detect_domain, domain_similarity
from app.services.job_skill_extractor import JobSkillProfile, extract_job_skill_profile
from app.services.skill_normalizer import (
    categorize_skill,
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


def _build_skill_depth(extracted_data: dict[str, Any]) -> tuple[set[str], set[str], dict[str, float]]:
    base_skills = set(flatten_skills(extracted_data.get("skills")))
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
        for token in extract_terms_from_text(project_text):
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
        for token in extract_terms_from_text(experience_text):
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
    base_skills = set(flatten_skills(extracted_data.get("skills")))
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
    min_skill_overlap = 0.3
    min_semantic_similarity = 0.4
    minimum_score = 0.6

    def __init__(self, user_profile: UserProfile, behavior_profile: BehaviorProfile | None = None) -> None:
        self.user = user_profile
        self.behavior = behavior_profile or BehaviorProfile({}, {}, {})
        self.user_skill_space = self.user.base_skills | self.user.project_skills | self.user.experience_skills
        self.expanded_user_skills = expand_with_related(self.user_skill_space)

    def evaluate_job(self, job: dict[str, Any], semantic_similarity_score: float) -> MatchResult:
        job_profile = extract_job_skill_profile(job)
        title = str(job.get("title") or "")
        location = str(job.get("location") or "")
        domain_score = domain_similarity(self.user.domain, job_profile.domain)
        if domain_score <= 0.10:
            return MatchResult(accepted=False, filter_reason="domain_mismatch", domain=job_profile.domain)

        relevant_job_skills = set(job_profile.required_skills or job_profile.critical_skills or job_profile.weighted_keywords)
        if not relevant_job_skills:
            relevant_job_skills = set(job_profile.weighted_keywords.keys())
        if not relevant_job_skills:
            return MatchResult(accepted=False, filter_reason="missing_job_skills", domain=job_profile.domain)

        matched_skills = self._match_skills(relevant_job_skills)
        skill_overlap = self._weighted_skill_match(job_profile, matched_skills)
        if skill_overlap < self.min_skill_overlap:
            return MatchResult(accepted=False, filter_reason="low_skill_overlap", domain=job_profile.domain)

        if semantic_similarity_score < self.min_semantic_similarity:
            return MatchResult(accepted=False, filter_reason="low_semantic_similarity", domain=job_profile.domain)

        role_match_score = self._role_match_score(title)
        if self.user.preferred_roles and role_match_score < 0.50:
            return MatchResult(accepted=False, filter_reason="role_mismatch", domain=job_profile.domain)

        location_match_score = self._location_match_score(location)
        if not self.user.remote_ok and self.user.preferred_locations and location_match_score <= 0.0:
            return MatchResult(accepted=False, filter_reason="location_mismatch", domain=job_profile.domain)

        project_relevance = self._project_relevance(job_profile)
        experience_depth = self._experience_depth(job_profile)
        behavior_score = compute_behavior_score(self.behavior, job_profile)

        final_score = (
            0.35 * skill_overlap
            + 0.20 * project_relevance
            + 0.15 * experience_depth
            + 0.15 * semantic_similarity_score
            + 0.10 * role_match_score
            + 0.05 * location_match_score
        )

        penalties: list[str] = []
        missing_critical = [skill for skill in job_profile.critical_skills if skill not in matched_skills]
        if domain_score < 0.45:
            final_score *= 0.85
            penalties.append("Partial domain mismatch")
        if skill_overlap < 0.30:
            final_score *= 0.3
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
                missing_skills=sorted(relevant_job_skills - matched_skills),
                penalties=penalties,
                filter_reason="below_threshold",
                domain=job_profile.domain,
                confidence_level=_confidence_level(final_score),
                selection_probability=round(final_score, 4),
            )

        reasons = self._build_reasons(
            matched_skills=matched_skills,
            role_match_score=role_match_score,
            location_match_score=location_match_score,
            project_relevance=project_relevance,
            experience_depth=experience_depth,
            semantic_similarity_score=semantic_similarity_score,
            job_domain=job_profile.domain,
        )
        skill_gaps = self._build_skill_gaps(sorted(relevant_job_skills - matched_skills))

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
            missing_skills=sorted(relevant_job_skills - matched_skills),
            skill_gaps=skill_gaps,
            reasons=reasons,
            penalties=penalties,
            domain=job_profile.domain,
            confidence_level=_confidence_level(final_score),
            selection_probability=round(final_score, 4),
        )

    def _match_skills(self, job_skills: set[str]) -> set[str]:
        matched: set[str] = set()
        for skill in job_skills:
            related = get_related_skills(skill)
            if related & self.expanded_user_skills:
                matched.add(skill)
        return matched

    def _weighted_skill_match(self, job_profile: JobSkillProfile, matched_skills: set[str]) -> float:
        total_weight = sum(job_profile.weighted_keywords.values()) or len(job_profile.weighted_keywords) or 1
        matched_weight = sum(
            weight
            for skill, weight in job_profile.weighted_keywords.items()
            if skill in matched_skills
        )
        cooccurrence_boost = min(0.12, 0.04 * job_profile.related_skill_groups_hit)
        return _clip01((matched_weight / total_weight) + cooccurrence_boost)

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
        role_match_score: float,
        location_match_score: float,
        project_relevance: float,
        experience_depth: float,
        semantic_similarity_score: float,
        job_domain: str,
    ) -> list[str]:
        reasons: list[str] = []
        if matched_skills:
            reasons.append(f"Strong match: {', '.join(sorted(matched_skills)[:4])}")
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
        return reasons[:4] or ["High-signal match after strict relevance filtering"]

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
