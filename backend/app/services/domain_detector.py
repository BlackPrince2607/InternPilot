from __future__ import annotations

from collections import Counter

from app.services.skill_normalizer import extract_terms_from_text, normalize_skill

# EXPANDED
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
        "spring",
        "hibernate",
        "grpc",
        "graphql",
        "kafka",
        "rabbitmq",
        "celery",
        "rest api",
        "microservice",
        "golang",
        "scala",
        ".net",
        "c#",
        "php",
        "ruby",
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
        "svelte",
        "remix",
        "nuxt",
        "vite",
        "webpack",
        "tailwind",
        "sass",
        "less",
        "storybook",
        "responsive",
        "accessibility",
        "a11y",
    },
    "ml": {
        "machine learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit learn",
        "scikit-learn",
        "computer vision",
        "nlp",
        "ml",
        "ai",
        "xgboost",
        "lightgbm",
        "opencv",
        "nltk",
        "spacy",
        "hugging face",
        "langchain",
        "generative ai",
        "llm",
        "rag",
        "yolo",
        "recommendation",
        "classification",
        "regression",
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
        "tableau",
        "power bi",
        "looker",
        "dbt",
        "snowflake",
        "bigquery",
        "redshift",
        "kafka",
        "pipeline",
        "warehouse",
        "lakehouse",
        "elt",
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
        "ansible",
        "helm",
        "argocd",
        "jenkins",
        "github actions",
        "gitlab ci",
        "prometheus",
        "grafana",
        "elk",
        "splunk",
        "reliability",
        "infrastructure",
    },
    "mobile": {
        "android",
        "ios",
        "flutter",
        "react native",
        "swift",
        "kotlin",
        "mobile",
        "expo",
        "swiftui",
        "jetpack compose",
        "xamarin",
        "ionic",
        "capacitor",
        "xcode",
        "android studio",
    },
}

# EXPANDED
DOMAIN_SIMILARITY = {
    ("backend", "backend"): 1.0,
    ("backend", "data"): 0.55,
    ("backend", "ml"): 0.45,
    ("backend", "devops"): 0.65,
    ("backend", "frontend"): 0.35,
    ("backend", "mobile"): 0.25,
    ("frontend", "frontend"): 1.0,
    ("frontend", "mobile"): 0.65,
    ("frontend", "backend"): 0.35,
    ("frontend", "data"): 0.15,
    ("ml", "ml"): 1.0,
    ("ml", "data"): 0.75,
    ("ml", "backend"): 0.45,
    ("data", "data"): 1.0,
    ("data", "ml"): 0.75,
    ("data", "backend"): 0.55,
    ("devops", "devops"): 1.0,
    ("devops", "backend"): 0.65,
    ("mobile", "mobile"): 1.0,
    ("mobile", "frontend"): 0.65,
    ("general", "general"): 0.6,
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


# EXPANDED
def detect_domains_multi(text: str, skills: list[str] | set[str] | None = None) -> list[str]:
    tokens = set(extract_terms_from_text(text or ""))
    if skills:
        tokens.update(normalize_skill(skill) for skill in skills if skill)

    counts: Counter[str] = Counter()
    lowered_text = (text or "").lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        counts[domain] = sum(1 for keyword in keywords if keyword in tokens or keyword in lowered_text)

    if not counts or max(counts.values()) == 0:
        return ["general"]

    max_count = max(counts.values())
    threshold = max(1, max_count * 0.6)
    return [domain for domain, count in counts.items() if count >= threshold] or ["general"]


def domains_compatible(user_domain: str, job_domain: str) -> bool:
    return domain_similarity(user_domain, job_domain) >= 0.30


def domain_similarity(user_domain: str, job_domain: str) -> float:
    if user_domain == "general" or job_domain == "general":
        return 0.6
    if user_domain == job_domain:
        return 1.0
    return DOMAIN_SIMILARITY.get((user_domain, job_domain), DOMAIN_SIMILARITY.get((job_domain, user_domain), 0.0))
