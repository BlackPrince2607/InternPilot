from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

# EXPANDED
SKILL_SYNONYMS = {
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "vue js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "angular js": "angular",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node js": "node.js",
    "node": "node.js",
    "node js runtime": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "express js": "express",
    "nextjs": "next.js",
    "next.js": "next.js",
    "next js": "next.js",
    "next": "next.js",
    "nuxtjs": "nuxt.js",
    "nuxt js": "nuxt.js",
    "nuxt": "nuxt.js",
    "nestjs": "nest.js",
    "nest js": "nest.js",
    "py": "python",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "skl": "scikit-learn",
    "tf": "tensorflow",
    "torch": "pytorch",
    "hf": "hugging face",
    "huggingface": "hugging face",
    "transformers": "hugging face",
    "langchain": "langchain",
    "lc": "langchain",
    "fastapi": "fastapi",
    "flask": "flask",
    "django": "django",
    "celery": "celery",
    "golang": "go",
    "go lang": "go",
    "dotnet": ".net",
    "dot net": ".net",
    "net": ".net",
    "c sharp": "c#",
    "csharp": "c#",
    "asp.net": ".net",
    "asp net": ".net",
    "aspnet": ".net",
    "springboot": "spring boot",
    "spring-boot": "spring boot",
    "spring boot": "spring boot",
    "jpa": "spring boot",
    "hibernate": "hibernate",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "dynamo": "dynamodb",
    "dynamodb": "dynamodb",
    "elastic": "elasticsearch",
    "es": "elasticsearch",
    "redis": "redis",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "supabase": "supabase",
    "firebase": "firebase",
    "firestore": "firebase",
    "cassandra": "cassandra",
    "couch": "couchdb",
    "neo4j": "neo4j",
    "pinecone": "pinecone",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "aws ec2": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "k8s": "kubernetes",
    "k8": "kubernetes",
    "kube": "kubernetes",
    "docker": "docker",
    "terraform": "terraform",
    "tf cloud": "terraform",
    "ansible": "ansible",
    "helm": "helm",
    "gh actions": "github actions",
    "gha": "github actions",
    "github action": "github actions",
    "gitlab ci": "gitlab ci/cd",
    "gitlab ci cd": "gitlab ci/cd",
    "gitlab cicd": "gitlab ci/cd",
    "jenkins": "jenkins",
    "circleci": "circleci",
    "argocd": "argocd",
    "argo cd": "argocd",
    "rn": "react native",
    "react-native": "react native",
    "react native": "react native",
    "flutter": "flutter",
    "swiftui": "swift",
    "jetpack": "kotlin",
    "jetpack compose": "kotlin",
    "expo": "react native",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "power bi": "power bi",
    "tableau": "tableau",
    "looker": "looker",
    "dbt": "dbt",
    "airflow": "apache airflow",
    "apache airflow": "apache airflow",
    "spark": "apache spark",
    "apache spark": "apache spark",
    "kafka": "apache kafka",
    "apache kafka": "apache kafka",
    "hadoop": "hadoop",
    "hive": "hive",
    "pig": "pig",
    "flink": "apache flink",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "bq": "bigquery",
    "redshift": "redshift",
    "cv": "computer vision",
    "nlp": "natural language processing",
    "rl": "reinforcement learning",
    "dl": "deep learning",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "genai": "generative ai",
    "gen ai": "generative ai",
    "llm": "large language models",
    "llms": "large language models",
    "rag": "retrieval augmented generation",
    "xgboost": "xgboost",
    "lgbm": "lightgbm",
    "lightgbm": "lightgbm",
    "yolo": "yolo",
    "opencv": "opencv",
    "cv2": "opencv",
    "nltk": "nltk",
    "spacy": "spacy",
    "keras": "keras",
    "jax": "jax",
    "gh": "github",
    "git hub": "github",
    "gl": "gitlab",
    "git lab": "gitlab",
    "bb": "bitbucket",
    "selenium": "selenium",
    "cypress": "cypress",
    "playwright": "playwright",
    "jest": "jest",
    "pytest": "pytest",
    "junit": "junit",
    "postman": "postman",
    "insomnia": "insomnia",
    "swagger": "swagger",
    "graphql": "graphql",
    "grpc": "grpc",
    "rest": "rest api",
    "restful": "rest api",
    "restful api": "rest api",
    "rest apis": "rest api",
    "ci cd": "ci/cd",
    "websocket": "websockets",
    "web socket": "websockets",
}

NOISE_TOKENS = {
    "and",
    "with",
    "using",
    "build",
    "built",
    "project",
    "projects",
    "experience",
    "work",
    "developer",
    "intern",
    "team",
}

SKILL_INFERENCE_MAP = {
    "react": {"javascript", "frontend", "web"},
    "next.js": {"react", "javascript", "frontend"},
    "node.js": {"backend", "javascript", "api"},
    "nodejs": {"backend", "javascript", "api"},
    "express": {"node.js", "backend", "api"},
    "fastapi": {"python", "backend", "api"},
    "django": {"python", "backend", "api"},
    "flask": {"python", "backend", "api"},
}

# EXPANDED
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
        "r",
        "scala",
        "dart",
        "bash",
        ".net",
        "shell",
        "matlab",
        "elixir",
        "lua",
        "perl",
    },
    "frameworks": {
        "fastapi",
        "django",
        "flask",
        "react",
        "next.js",
        "vue",
        "angular",
        "spring",
        "spring boot",
        "hibernate",
        "laravel",
        "node.js",
        "nodejs",
        "express",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "flutter",
        "react native",
        "scikit-learn",
        "xgboost",
        "lightgbm",
        "keras",
        "opencv",
        "langchain",
        "hugging face",
        "nuxt.js",
        "nest.js",
        "svelte",
        "graphql",
        "grpc",
        "celery",
        "scrapy",
        "expo",
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
        "terraform",
        "ansible",
        "helm",
        "argocd",
        "jenkins",
        "github actions",
        "gitlab ci/cd",
        "prometheus",
        "grafana",
        "selenium",
        "cypress",
        "playwright",
        "jest",
        "webpack",
        "vite",
        "swagger",
        "tableau",
        "power bi",
        "looker",
        "storybook",
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
        "cassandra",
        "dynamodb",
        "neo4j",
        "snowflake",
        "bigquery",
        "redshift",
        "pinecone",
        "cockroachdb",
        "influxdb",
        "couchdb",
    },
    "data_tools": {
        "apache spark",
        "apache kafka",
        "apache airflow",
        "hadoop",
        "hive",
        "dbt",
        "flink",
        "prefect",
        "dagster",
    },
}

# EXPANDED
RELATED_SKILL_GROUPS = [
    {"fastapi", "django", "flask", "spring boot", "express", "gin"},
    {"react", "vue", "angular", "svelte", "nuxt.js"},
    {"postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra"},
    {"docker", "kubernetes", "helm"},
    {"tensorflow", "pytorch", "scikit-learn", "keras", "jax"},
    {"node.js", "express", "nest.js"},
    {"nodejs", "express", "nest.js"},
    {"aws", "google cloud", "azure"},
    {"github actions", "gitlab ci/cd", "jenkins", "circleci"},
    {"apache spark", "apache kafka", "apache airflow", "hadoop"},
    {"langchain", "hugging face", "openai"},
    {"tableau", "power bi", "looker"},
    {"react native", "flutter", "expo"},
    {"graphql", "grpc", "rest api"},
    {"prometheus", "grafana", "elasticsearch"},
    {"terraform", "ansible", "helm", "argocd"},
    {"xgboost", "lightgbm", "scikit-learn"},
    {"selenium", "cypress", "playwright", "jest"},
]


@lru_cache(maxsize=4096)
def normalize_skill(value: str) -> str:
    normalized = re.sub(r"[\.\-_\/]+", " ", str(value or "").strip().lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = SKILL_SYNONYMS.get(normalized, normalized)

    # Singularize basic plural skill forms (e.g., APIs -> api).
    tokens: list[str] = []
    for token in normalized.split():
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    normalized = " ".join(tokens).strip()

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
            if normalized and normalized not in NOISE_TOKENS and normalized not in seen:
                seen.add(normalized)
                values.append(normalized)
    return values


def enrich_resume_skills(skills: list[str] | set[str]) -> set[str]:
    normalized = {normalize_skill(skill) for skill in skills if normalize_skill(skill)}
    enriched = set(normalized)
    for skill in list(normalized):
        enriched.update(SKILL_INFERENCE_MAP.get(skill, set()))
    return {skill for skill in enriched if skill and skill not in NOISE_TOKENS}


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
    for key in ("languages", "frameworks", "tools", "databases", "data_tools", "skills", "core"):
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
