from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.services.domain_detector import detect_domain
from app.services.skill_normalizer import extract_terms_from_text, flatten_skills, normalize_skill


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


@dataclass(slots=True)
class JobSkillProfile:
    title_skills: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    description_skills: list[str] = field(default_factory=list)
    weighted_keywords: dict[str, int] = field(default_factory=dict)
    critical_skills: list[str] = field(default_factory=list)
    domain: str = "general"
    full_text: str = ""
    related_skill_groups_hit: int = 0


def extract_job_skill_profile(job: dict[str, Any]) -> JobSkillProfile:
    raw_data = _as_dict(job.get("raw_data"))
    title = str(job.get("title") or "")
    description = str(job.get("description") or "")

    title_skills = extract_terms_from_text(title)
    required_candidates: list[Any] = [job.get("skills_required")]
    for key in ("skills_required", "skills", "required_skills", "technologies", "tech_stack", "tags"):
        if raw_data.get(key):
            required_candidates.append(raw_data.get(key))

    required_skills: list[str] = []
    for candidate in required_candidates:
        required_skills.extend(flatten_skills(candidate))
    required_skills = list(dict.fromkeys(normalize_skill(skill) for skill in required_skills if skill))

    description_skills = extract_terms_from_text(description)

    weights: Counter[str] = Counter()
    for skill in title_skills:
        weights[skill] += 3
    for skill in required_skills:
        weights[skill] += 2
    for skill in description_skills:
        weights[skill] += 1

    critical_skills = [
        skill
        for skill, weight in sorted(weights.items(), key=lambda item: (-item[1], item[0]))
        if weight >= 3
    ][:8]
    related_group_count = 0
    skill_set = set(weights.keys())
    related_groups = [
        {"fastapi", "django", "flask"},
        {"react", "vue", "angular"},
        {"postgresql", "mysql", "sqlite", "mongodb", "redis"},
        {"docker", "kubernetes"},
        {"tensorflow", "pytorch", "scikit learn"},
    ]
    for group in related_groups:
        if len(skill_set & group) >= 2:
            related_group_count += 1

    domain, _ = detect_domain(
        f"{title}\n{description}",
        skills=list(weights.keys()),
    )

    return JobSkillProfile(
        title_skills=title_skills,
        required_skills=required_skills,
        description_skills=description_skills,
        weighted_keywords=dict(weights),
        critical_skills=critical_skills,
        domain=domain,
        full_text=f"{title}\n{description}".strip(),
        related_skill_groups_hit=related_group_count,
    )
