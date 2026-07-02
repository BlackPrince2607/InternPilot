from __future__ import annotations

import json
from typing import Any

LOCATION_ALIASES = {
    # Tier 1
    "bangalore": [
        "bangalore", "bengaluru", "bengalooru", "blr",
        "whitefield", "koramangala", "indiranagar",
        "electronic city", "marathahalli", "hsr layout",
        "jp nagar", "sarjapur", "hebbal", "yeshwanthpur"
    ],
    "delhi ncr": [
        "delhi", "new delhi", "ncr", "delhi ncr",
        "gurgaon", "gurugram", "noida", "faridabad",
        "ghaziabad", "greater noida", "manesar", "dwarka"
    ],
    "mumbai": [
        "mumbai", "bombay", "thane", "navi mumbai",
        "bandra", "andheri", "powai", "malad",
        "goregaon", "lower parel", "worli", "kurla"
    ],
    "hyderabad": [
        "hyderabad", "secunderabad", "cyberabad",
        "hitec city", "gachibowli", "madhapur",
        "kondapur", "jubilee hills", "begumpet"
    ],
    "chennai": [
        "chennai", "madras", "sholinganallur",
        "perungudi", "tidel park", "taramani",
        "guindy", "ambattur", "omr", "velachery"
    ],
    "pune": [
        "pune", "pimpri", "chinchwad", "hinjewadi",
        "wakad", "baner", "kothrud", "viman nagar",
        "hadapsar", "magarpatta", "kharadi", "bund garden"
    ],

    # Tier 2
    "kolkata": [
        "kolkata", "calcutta", "salt lake",
        "sector v", "new town", "rajarhat", "howrah"
    ],
    "ahmedabad": [
        "ahmedabad", "gandhinagar", "sg highway",
        "prahlad nagar", "navrangpura", "satellite"
    ],
    "jaipur": [
        "jaipur", "pink city", "malviya nagar",
        "vaishali nagar", "tonk road"
    ],
    "chandigarh": [
        "chandigarh", "mohali", "panchkula",
        "tricity", "zirakpur"
    ],
    "kochi": [
        "kochi", "cochin", "ernakulam",
        "kakkanad", "infopark", "technopark"
    ],
    "indore": ["indore", "vijay nagar", "palasia"],
    "bhubaneswar": [
        "bhubaneswar", "bbsr", "infocity",
        "patia", "chandrasekharpur"
    ],
    "coimbatore": ["coimbatore", "kovai", "peelamedu"],
    "vizag": [
        "vizag", "visakhapatnam", "vishakhapatnam",
        "mvp colony", "rushikonda"
    ],
    "noida": [
        "noida", "greater noida", "sector 62",
        "sector 63", "sector 132", "sector 135"
    ],

    # Remote variants
    "remote": [
        "remote", "work from home", "wfh",
        "work-from-home", "fully remote", "100% remote",
        "anywhere", "virtual", "home based",
        "home-based", "distributed", "online"
    ],
    "hybrid": [
        "hybrid", "hybrid remote", "partially remote",
        "flexible", "wfh + office", "office + wfh",
        "2 days remote", "3 days remote"
    ],
    "pan india": [
        "pan india", "all india", "anywhere in india",
        "multiple locations", "various locations",
        "india", "nationwide"
    ],
}

# EXPANDED
ROLE_SYNONYMS = {
    "backend intern": [
        "backend", "back end", "back-end",
        "software engineer", "sde", "software development",
        "server side", "server-side", "api developer",
        "python developer", "java developer", "node developer",
        "golang developer", "backend developer",
        "software intern", "engineering intern",
        "technology analyst", "tech analyst"
    ],
    "frontend intern": [
        "frontend", "front end", "front-end",
        "ui developer", "ui/ux developer",
        "react developer", "angular developer",
        "vue developer", "web developer",
        "javascript developer", "software engineer",
        "software intern", "engineering intern"
    ],
    "full stack intern": [
        "full stack", "fullstack", "full-stack",
        "software engineer", "sde", "web developer",
        "software developer", "engineering intern",
        "software intern", "technology analyst"
    ],
    "ml/ai intern": [
        "machine learning", "ml engineer", "ai engineer",
        "deep learning", "data scientist", "research intern",
        "nlp engineer", "computer vision", "mlops",
        "research engineer", "applied scientist",
        "ml intern", "ai intern", "data science intern"
    ],
    "data science intern": [
        "data science", "data scientist", "data analyst",
        "analytics", "business intelligence", "bi analyst",
        "data engineer", "data intern", "analyst intern",
        "research analyst", "insights analyst"
    ],
    "devops intern": [
        "devops", "dev ops", "sre", "site reliability",
        "platform engineer", "infrastructure", "cloud engineer",
        "systems engineer", "release engineer",
        "build engineer", "operations engineer"
    ],
    "mobile intern": [
        "mobile developer", "android developer",
        "ios developer", "flutter developer",
        "react native developer", "mobile engineer",
        "app developer", "android intern", "ios intern"
    ],
    "data engineer intern": [
        "data engineer", "etl developer", "pipeline engineer",
        "data infrastructure", "data platform",
        "analytics engineer", "warehouse engineer"
    ],
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
    if not pref or not job_location:
        return False
    pref_norm = normalize_skill(pref).lower()
    location_norm = normalize_skill(job_location).lower()

    if pref_norm in location_norm or location_norm in pref_norm:
        return True

    remote_signals = [
        "remote", "work from home", "wfh", "anywhere",
        "fully remote", "virtual", "home based", "distributed"
    ]
    if pref_norm in ("remote", "wfh", "work from home"):
        return any(s in location_norm for s in remote_signals)

    if pref_norm in ("pan india", "india", "all india"):
        return True

    aliases = LOCATION_ALIASES.get(pref_norm, [])
    return any(alias in location_norm for alias in aliases)


def role_matches_title(role: str, title: str) -> bool:
    role_norm = normalize_skill(role)
    title_norm = normalize_skill(title)

    synonyms = ROLE_SYNONYMS.get(role_norm, [])
    if synonyms and any(normalize_skill(syn) in title_norm for syn in synonyms):
        return True

    if role_norm in title_norm:
        return True

    role_words = [word for word in role_norm.split() if word and len(word) > 2]
    title_words = set(word for word in title_norm.split() if word)
    if not role_words or not title_words:
        return False

    matched = sum(1 for word in role_words if word in title_words)
    threshold = max(1, len(role_words) // 2)
    return matched >= threshold
