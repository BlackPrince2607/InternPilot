from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from bs4 import BeautifulSoup

from app.scraper.utils import normalize_company_name, normalize_location, normalize_whitespace

SPAM_PATTERNS = [
    r"\burgent hiring\b",
    r"\bwalk[- ]?in\b",
    r"\bimmediate joiner\b",
    r"\bapply now\b",
    r"\bcall now\b",
    r"\bwhatsapp\b",
]

NON_TECH_SIGNALS = {
    "marketing",
    "sales",
    "business development",
    "hr",
    "human resources",
    "recruiter",
    "telecaller",
    "operations executive",
}


@dataclass(slots=True)
class CleanedJob:
    title: str
    company: str
    location: str
    description: str
    apply_url: str
    posted_at: str | None
    source: str
    raw_data: dict[str, Any]


def clean_html(text: str | None) -> str:
    html = str(text or "")
    if not html:
        return ""
    return normalize_whitespace(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))


def clean_job_payload(payload: dict[str, Any]) -> CleanedJob:
    description = clean_html(payload.get("description"))
    for pattern in SPAM_PATTERNS:
        description = re.sub(pattern, " ", description, flags=re.IGNORECASE)
    description = normalize_whitespace(description)

    posted_at = payload.get("posted_at")
    if isinstance(posted_at, datetime):
        posted_at = posted_at.astimezone(UTC).isoformat()
    elif posted_at is not None:
        posted_at = str(posted_at)

    return CleanedJob(
        title=normalize_whitespace(str(payload.get("title") or "")),
        company=normalize_company_name(str(payload.get("company") or "")),
        location=normalize_location(str(payload.get("location") or "")) or "Remote",
        description=description,
        apply_url=normalize_whitespace(str(payload.get("apply_url") or "")),
        posted_at=posted_at,
        source=normalize_whitespace(str(payload.get("source") or "")),
        raw_data=payload.get("raw_data") or {},
    )


def is_low_information_job(cleaned: CleanedJob, min_description_chars: int = 100) -> bool:
    if not cleaned.title or not cleaned.company or not cleaned.apply_url:
        return True
    if len(cleaned.description) < min_description_chars:
        return True
    blob = f"{cleaned.title} {cleaned.description}".lower()
    return any(signal in blob for signal in NON_TECH_SIGNALS)
