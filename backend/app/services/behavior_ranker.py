from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.services.domain_detector import detect_domain
from app.services.job_skill_extractor import extract_job_skill_profile

ACTION_WEIGHTS = {
    "view": 1.0,
    "apply": 2.0,
    "skip": -1.5,
}


@dataclass(slots=True)
class BehaviorProfile:
    domain_preferences: dict[str, float]
    skill_preferences: dict[str, float]
    title_preferences: dict[str, float]


# EXPANDED
def _get_warm_defaults(user_domain: str) -> BehaviorProfile:
    domain_boost = {user_domain: 2.0} if user_domain != "general" else {}
    return BehaviorProfile(
        domain_preferences=domain_boost,
        skill_preferences={},
        title_preferences={},
    )


def load_behavior_profile(supabase, user_id: str) -> BehaviorProfile:
    try:
        result = (
            supabase.table("user_interactions")
            .select("action,jobs:job_id(title,description,skills_required,raw_data)")
            .eq("user_id", user_id)
            .limit(500)
            .execute()
        )
    except Exception:
        return BehaviorProfile(domain_preferences={}, skill_preferences={}, title_preferences={})

    domain_counter: Counter[str] = Counter()
    skill_counter: Counter[str] = Counter()
    title_counter: defaultdict[str, float] = defaultdict(float)

    for row in result.data or []:
        action = str(row.get("action") or "").lower()
        weight = ACTION_WEIGHTS.get(action)
        if weight is None:
            continue
        job = row.get("jobs") or {}
        profile = extract_job_skill_profile(job)
        domain, _ = detect_domain(profile.full_text, skills=list(profile.weighted_keywords.keys()))
        if domain:
            domain_counter[domain] += weight
        for skill in profile.critical_skills[:5]:
            skill_counter[skill] += weight
        for skill in profile.title_skills[:4]:
            title_counter[skill] += weight

    profile = BehaviorProfile(
        domain_preferences=dict(domain_counter),
        skill_preferences=dict(skill_counter),
        title_preferences=dict(title_counter),
    )

    # EXPANDED
    if (
        not profile.domain_preferences
        and not profile.skill_preferences
        and not profile.title_preferences
    ):
        return BehaviorProfile(
            domain_preferences={},
            skill_preferences={},
            title_preferences={},
        )
    return profile


def compute_behavior_score(profile: BehaviorProfile, job_profile) -> float:
    has_history = bool(profile.domain_preferences or profile.skill_preferences or profile.title_preferences)
    if not has_history:
        return 0.55

    domain_pref = profile.domain_preferences.get(job_profile.domain, 0.0)
    critical = sum(profile.skill_preferences.get(skill, 0.0) for skill in job_profile.critical_skills[:5])
    title = sum(profile.title_preferences.get(skill, 0.0) for skill in job_profile.title_skills[:4])

    raw_score = 0.5 + 0.08 * domain_pref + 0.03 * critical + 0.02 * title
    return max(0.0, min(1.0, raw_score))
