from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from app.utils.matching import location_matches, normalize_terms, role_matches_title


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _to_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    return None


def get_recency_score(posted_at: Any) -> float:
    dt = _to_datetime(posted_at)
    if not dt:
        return 0.3

    age_days = max(
        0.0,
        (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 86400.0,
    )

    if age_days <= 1:
        return 1.0
    if age_days <= 3:
        return 0.8
    if age_days <= 7:
        return 0.6
    return 0.3


def compute_keyword_score(job: Dict[str, Any], preferences: Dict[str, Any]) -> float:
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()

    preferred_roles: Iterable[str] = preferences.get("preferred_roles") or []
    preferred_locations: Iterable[str] = preferences.get("preferred_locations") or []

    role_terms = normalize_terms(list(preferred_roles))
    location_terms = normalize_terms(list(preferred_locations))

    role_hit = 1.0 if role_terms and any(role_matches_title(term, title) for term in role_terms) else 0.0
    location_hit = 1.0 if location_terms and any(location_matches(term, location) for term in location_terms) else 0.0

    if not role_terms and not location_terms:
        return 0.5

    components = []
    if role_terms:
        components.append(role_hit)
    if location_terms:
        components.append(location_hit)

    return round(sum(components) / len(components), 4) if components else 0.5


def compute_job_score(job: Dict[str, Any], match_score: float, preferences: Dict[str, Any]) -> Dict[str, float]:
    match_norm = float(match_score or 0.0)
    if match_norm > 1.0:
        match_norm = match_norm / 100.0
    match_norm = _clamp01(match_norm)

    company = job.get("companies") or {}
    company_quality = float(company.get("quality_score") or job.get("company_quality_score") or 0.0)
    company_score = company_quality / 100.0 if company_quality > 1.0 else company_quality
    company_score = _clamp01(company_score)

    recency_score = get_recency_score(job.get("posted_at"))
    keyword_score = compute_keyword_score(job, preferences or {})

    final_score = (
        0.50 * match_norm
        + 0.20 * keyword_score
        + 0.15 * recency_score
        + 0.15 * company_score
    )

    return {
        "final_score": round(_clamp01(final_score), 6),
        "company_score": round(company_score, 6),
        "recency_score": round(recency_score, 6),
        "keyword_score": round(keyword_score, 6),
    }
