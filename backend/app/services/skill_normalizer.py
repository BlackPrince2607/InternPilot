from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

SKILL_SYNONYMS = {
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "nodejs": "node.js",
    "node": "node.js",
    "expressjs": "express",
    "nextjs": "next.js",
    "py": "python",
    "tf": "tensorflow",
    "k8s": "kubernetes",
    "gcp": "google cloud",
    "aws ec2": "aws",
}

SKILL_CATEGORIES = {
    "core": {
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "go",
        "rust",
        "swift",
        "kotlin",
        "sql",
    },
    "frameworks": {
        "fastapi",
        "django",
        "flask",
        "react",
        "next.js",
        "vue",
        "angular",
        "spring boot",
        "node.js",
        "express",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "flutter",
        "react native",
    },
    "tools": {
        "docker",
        "git",
        "github",
        "kubernetes",
        "aws",
        "google cloud",
        "azure",
        "linux",
        "postman",
        "figma",
        "jira",
        "ci/cd",
    },
    "databases": {
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "sqlite",
        "supabase",
        "firebase",
        "elasticsearch",
    },
}

RELATED_SKILL_GROUPS = [
    {"fastapi", "django", "flask"},
    {"react", "vue", "angular"},
    {"postgresql", "mysql", "sqlite", "mongodb", "redis"},
    {"docker", "kubernetes"},
    {"tensorflow", "pytorch", "scikit learn"},
    {"node.js", "express"},
]


@lru_cache(maxsize=4096)
def normalize_skill(value: str) -> str:
    normalized = re.sub(r"[\.\-_\/]+", " ", str(value or "").strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return SKILL_SYNONYMS.get(normalized, normalized)


def normalize_terms(raw: Any) -> list[str]:
    if raw is None:
        return []

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        items = [raw]
    else:
        items = [str(raw)]

    values: list[str] = []
    seen: set[str] = set()
    for item in items:
        for part in re.split(r"[,|\n;/]+", str(item)):
            normalized = normalize_skill(part)
            if normalized and normalized not in seen:
                seen.add(normalized)
                values.append(normalized)
    return values


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
    for key in ("languages", "frameworks", "tools", "databases", "skills", "core"):
        value = categories.get(key, [])
        if isinstance(value, list):
            merged.extend(value)
        elif isinstance(value, str):
            merged.append(value)
    return normalize_terms(merged)


def categorize_skill(skill: str) -> str:
    normalized = normalize_skill(skill)
    for category, values in SKILL_CATEGORIES.items():
        if normalized in values:
            return category
    return "other"


def get_related_skills(skill: str) -> set[str]:
    normalized = normalize_skill(skill)
    related = {normalized}
    for group in RELATED_SKILL_GROUPS:
        if normalized in group:
            related.update(group)
    return related


def expand_with_related(skills: set[str]) -> set[str]:
    expanded: set[str] = set()
    for skill in skills:
        expanded.update(get_related_skills(skill))
    return expanded


def extract_terms_from_text(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9\.\+#-]+", text or "")
    return normalize_terms(tokens)
