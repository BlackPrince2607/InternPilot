from __future__ import annotations

from collections import Counter

from app.services.skill_normalizer import extract_terms_from_text, normalize_skill

DOMAIN_KEYWORDS = {
    "backend": {
        "python",
        "java",
        "fastapi",
        "django",
        "flask",
        "spring boot",
        "node.js",
        "express",
        "api",
        "backend",
        "microservices",
        "postgresql",
        "mysql",
        "redis",
    },
    "frontend": {
        "react",
        "next.js",
        "vue",
        "angular",
        "frontend",
        "html",
        "css",
        "javascript",
        "typescript",
        "ui",
        "web",
    },
    "ml": {
        "machine learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit learn",
        "computer vision",
        "nlp",
        "ml",
        "ai",
    },
    "data": {
        "data",
        "analytics",
        "sql",
        "etl",
        "spark",
        "airflow",
        "pandas",
        "numpy",
        "business intelligence",
        "data engineering",
    },
    "devops": {
        "docker",
        "kubernetes",
        "aws",
        "google cloud",
        "azure",
        "terraform",
        "devops",
        "ci/cd",
        "linux",
        "sre",
    },
    "mobile": {
        "android",
        "ios",
        "flutter",
        "react native",
        "swift",
        "kotlin",
        "mobile",
    },
}

DOMAIN_SIMILARITY = {
    ("backend", "backend"): 1.0,
    ("backend", "data"): 0.45,
    ("backend", "ml"): 0.35,
    ("backend", "devops"): 0.55,
    ("backend", "frontend"): 0.25,
    ("backend", "mobile"): 0.15,
    ("frontend", "frontend"): 1.0,
    ("frontend", "mobile"): 0.55,
    ("frontend", "backend"): 0.25,
    ("frontend", "data"): 0.05,
    ("ml", "ml"): 1.0,
    ("ml", "data"): 0.65,
    ("ml", "backend"): 0.35,
    ("data", "data"): 1.0,
    ("data", "ml"): 0.65,
    ("data", "backend"): 0.45,
    ("devops", "devops"): 1.0,
    ("devops", "backend"): 0.55,
    ("mobile", "mobile"): 1.0,
    ("mobile", "frontend"): 0.55,
}


def detect_domain(text: str, skills: list[str] | set[str] | None = None) -> tuple[str, dict[str, int]]:
    tokens = set(extract_terms_from_text(text or ""))
    if skills:
        tokens.update(normalize_skill(skill) for skill in skills if skill)

    counts: Counter[str] = Counter()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        counts[domain] = sum(1 for keyword in keywords if keyword in tokens or keyword in (text or "").lower())

    if not counts or max(counts.values()) <= 0:
        return "general", dict(counts)
    best = counts.most_common(1)[0][0]
    return best, dict(counts)


def domains_compatible(user_domain: str, job_domain: str) -> bool:
    return domain_similarity(user_domain, job_domain) >= 0.30


def domain_similarity(user_domain: str, job_domain: str) -> float:
    if user_domain == "general" or job_domain == "general":
        return 0.6
    if user_domain == job_domain:
        return 1.0
    return DOMAIN_SIMILARITY.get((user_domain, job_domain), DOMAIN_SIMILARITY.get((job_domain, user_domain), 0.0))
