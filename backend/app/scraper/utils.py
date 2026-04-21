import hashlib
import logging
import os
import random
import re
import time
from datetime import UTC, datetime, timedelta
from typing import Iterable

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER_NAME = "internpilot.scraper"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
    "image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

SKILL_TAXONOMY = {
    "languages": {
        "python": "Python",
        "java": "Java",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "c": "C",
        "c++": "C++",
        "c#": "C#",
        "go": "Go",
        "golang": "Go",
        "ruby": "Ruby",
        "php": "PHP",
        "kotlin": "Kotlin",
        "swift": "Swift",
        "rust": "Rust",
        "sql": "SQL",
    },
    "frameworks": {
        "react": "React",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "vue": "Vue",
        "angular": "Angular",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "express": "Express",
        "django": "Django",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "spring boot": "Spring Boot",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "pandas": "Pandas",
        "numpy": "NumPy",
    },
    "tools": {
        "git": "Git",
        "github": "GitHub",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "postman": "Postman",
        "linux": "Linux",
        "figma": "Figma",
        "jira": "Jira",
    },
    "databases": {
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "sqlite": "SQLite",
        "supabase": "Supabase",
        "firebase": "Firebase",
    },
}

COMPANY_SUFFIXES = {
    "inc",
    "inc.",
    "llc",
    "l.l.c",
    "ltd",
    "ltd.",
    "limited",
    "private limited",
    "pvt ltd",
    "pvt. ltd.",
    "technologies",
    "technology",
}

TOP_COMPANIES = {
    "google": 100,
    "alphabet": 100,
    "microsoft": 98,
    "amazon": 97,
    "meta": 97,
    "apple": 97,
    "netflix": 95,
    "openai": 95,
    "uber": 93,
    "linkedin": 92,
    "adobe": 92,
    "atlassian": 91,
    "salesforce": 91,
    "oracle": 90,
    "intel": 90,
    "nvidia": 94,
    "goldman sachs": 88,
    "jpmorgan": 88,
    "flipkart": 86,
    "swiggy": 84,
    "zomato": 84,
    "razorpay": 87,
    "cred": 84,
}


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def configure_logging(level: str = "INFO") -> None:
    logger = get_logger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def utc_days_ago_iso(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def build_retry_session(
    total_retries: int = 3,
    backoff_factor: float = 1.5,
    timeout_seconds: int = 20,
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "HEAD"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    session.request = _wrap_request_with_timeout(session.request, timeout_seconds)
    return session


def _wrap_request_with_timeout(request_fn, timeout_seconds: int):
    def _request(method: str, url: str, **kwargs):
        kwargs.setdefault("timeout", timeout_seconds)
        return request_fn(method, url, **kwargs)

    return _request


def polite_sleep(min_seconds: float, max_seconds: float) -> None:
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_company_name(name: str) -> str:
    normalized = normalize_whitespace(name)
    lowered = normalized.lower()
    for suffix in sorted(COMPANY_SUFFIXES, key=len, reverse=True):
        pattern = rf"(?:,|\s)+{re.escape(suffix)}$"
        lowered = re.sub(pattern, "", lowered, flags=re.IGNORECASE)
    lowered = normalize_whitespace(lowered)
    if not lowered:
        return normalized
    return " ".join(word.upper() if len(word) <= 3 else word.capitalize() for word in lowered.split())


def infer_company_domain(company_name: str) -> str | None:
    normalized = normalize_whitespace(company_name).lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return None

    parts = [part for part in normalized.split(" ") if part]
    if not parts:
        return None

    candidate = "".join(parts)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", candidate):
        return None

    return f"{candidate}.com"


def normalize_for_hash(value: str | None) -> str:
    normalized = normalize_whitespace(value).lower()
    return re.sub(r"\s+", " ", normalized)


def normalize_location(location: str) -> str:
    normalized = normalize_whitespace(location)
    lowered = normalized.lower()
    remote_aliases = {"remote", "work from home", "wfh", "remote / wfh", "hybrid/remote"}
    if lowered in remote_aliases or "remote" in lowered:
        return "Remote"
    return ", ".join(part.strip().title() for part in normalized.split(",") if part.strip())


def get_company_score(name: str) -> int:
    normalized = normalize_for_hash(normalize_company_name(name))
    if not normalized:
        return 50

    for company, score in TOP_COMPANIES.items():
        if company in normalized:
            return score
    return 50


def extract_skills(*sources: str | Iterable[str]) -> dict:
    raw_tokens: list[str] = []
    categories = {key: [] for key in SKILL_TAXONOMY}

    for source in sources:
        if not source:
            continue
        if isinstance(source, str):
            tokens = re.split(r"[,/|\n\r\t()]+", source)
        else:
            tokens = list(source)
        raw_tokens.extend(token for token in tokens if token)

    joined_text = " ".join(raw_tokens).lower()
    for category, vocabulary in SKILL_TAXONOMY.items():
        for needle, canonical in vocabulary.items():
            if re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", joined_text):
                categories[category].append(canonical)

    categories = {
        key: sorted(set(values), key=str.lower)
        for key, values in categories.items()
    }
    flat_skills = sorted({skill for values in categories.values() for skill in values}, key=str.lower)

    return {
        "raw": sorted(
            {normalize_whitespace(token) for token in raw_tokens if normalize_whitespace(token)},
            key=str.lower,
        ),
        "normalized": flat_skills,
        "categories": categories,
    }


def generate_external_id(title: str, company: str, apply_url: str) -> str:
    payload = "||".join(
        [
            normalize_for_hash(title),
            normalize_for_hash(company),
            normalize_for_hash(apply_url),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_required_env_vars() -> list[str]:
    return ["SUPABASE_URL", "SUPABASE_KEY"]


def get_missing_env_vars() -> list[str]:
    return [name for name in get_required_env_vars() if not os.getenv(name)]


def build_httpx_async_client(timeout_seconds: float = 20.0) -> httpx.AsyncClient:
    transport = httpx.AsyncHTTPTransport(retries=3)
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_seconds),
        transport=transport,
        follow_redirects=True,
        headers=DEFAULT_HEADERS,
    )
