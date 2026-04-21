from __future__ import annotations

import json
from typing import Any

LOCATION_ALIASES = {
    "delhi ncr": ["delhi", "new delhi", "gurgaon", "gurugram", "noida", "faridabad"],
    "bangalore": ["bengaluru", "bangalore"],
    "mumbai": ["mumbai", "bombay"],
    "hyderabad": ["hyderabad", "secunderabad"],
    "chennai": ["chennai", "madras"],
    "pune": ["pune", "pimpri"],
}


def normalize_skill(s: str) -> str:
    return str(s).strip().lower().replace(".", "").replace("-", " ")


def normalize_terms(raw: Any) -> list[str]:
    if raw is None:
        return []

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        items = [raw]
    else:
        items = [str(raw)]

    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        for part in str(item).split(","):
            value = normalize_skill(part)
            if value and value not in seen:
                seen.add(value)
                out.append(value)
    return out


def flatten_skills(skills_obj: Any) -> list[str]:
    if not skills_obj:
        return []

    if isinstance(skills_obj, list):
        return normalize_terms(skills_obj)

    if isinstance(skills_obj, str):
        try:
            parsed = json.loads(skills_obj)
        except Exception:
            return normalize_terms(skills_obj)
        if isinstance(parsed, (dict, list)):
            return flatten_skills(parsed)
        return normalize_terms(skills_obj)

    if not isinstance(skills_obj, dict):
        return []

    if isinstance(skills_obj.get("normalized"), list):
        return normalize_terms(skills_obj.get("normalized"))

    categories = skills_obj.get("categories", skills_obj)
    if not isinstance(categories, dict):
        return []

    merged: list[Any] = []
    for key in ("languages", "frameworks", "tools", "databases", "skills"):
        value = categories.get(key, [])
        if isinstance(value, list):
            merged.extend(value)
        elif isinstance(value, str):
            merged.append(value)

    return normalize_terms(merged)


def location_matches(pref: str, job_location: str) -> bool:
    pref_norm = normalize_skill(pref)
    location_norm = normalize_skill(job_location)
    if not pref_norm or not location_norm:
        return False

    if pref_norm == "remote":
        return "remote" in location_norm

    if pref_norm in location_norm:
        return True

    aliases = LOCATION_ALIASES.get(pref_norm, [])
    return any(alias in location_norm for alias in aliases)


def role_matches_title(role: str, title: str) -> bool:
    role_words = [word for word in normalize_skill(role).split() if word]
    title_words = set(word for word in normalize_skill(title).split() if word)
    if not role_words or not title_words:
        return False

    matched = sum(1 for word in role_words if word in title_words)
    threshold = max(1, len(role_words) // 2)
    return matched >= threshold
