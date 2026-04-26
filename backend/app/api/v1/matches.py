from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client
from app.services.behavior_ranker import load_behavior_profile
from app.services.embedding_service import get_embedding
from app.services.match_engine import MatchEngine, build_user_profile
from app.services.retrieval_engine import RetrievalEngine
from app.utils.matching import location_matches, role_matches_title

router = APIRouter(prefix="/matches", tags=["matches"])
logger = logging.getLogger(__name__)

_JOB_SELECT = """
    id,
    company_id,
    external_id,
    title,
    location,
    remote_type,
    description,
    apply_url,
    source_name,
    experience_level,
    posted_at,
    stipend,
    score,
    is_active,
    skills_required,
    raw_data,
    job_domain,
    job_embedding,
    companies:company_id(id,name,careers_url,quality_score)
"""

_DEBUG_REASON_KEYS = (
    "low_skill_overlap",
    "low_semantic_similarity",
    "role_mismatch",
    "location_mismatch",
    "below_threshold",
)

_ADAPTIVE_MINIMUM_SCORE = 0.38
_ADAPTIVE_MIN_STRICT_MATCHES = 12
_COLUMN_EXISTS_CACHE: dict[tuple[str, str], bool] = {}
_BULK_SCORE_RPC_AVAILABLE: bool | None = None
_RESUME_EMBEDDING_WARNING_EMITTED = False


def _column_exists(supabase, table_name: str, column_name: str) -> bool:
    key = (table_name, column_name)
    cached = _COLUMN_EXISTS_CACHE.get(key)
    if cached is not None:
        return cached

    try:
        supabase.table(table_name).select(column_name).limit(1).execute()
        _COLUMN_EXISTS_CACHE[key] = True
    except Exception as exc:
        message = str(exc).lower()
        if "column" in message and "does not exist" in message:
            _COLUMN_EXISTS_CACHE[key] = False
        else:
            # Unknown error type: prefer conservative behavior.
            _COLUMN_EXISTS_CACHE[key] = False
    return _COLUMN_EXISTS_CACHE[key]


def _resume_embedding_column_exists(supabase) -> bool:
    return _column_exists(supabase, "resumes", "resume_embedding")


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_stipend(stipend_str: str | None) -> int:
    """Extract monthly stipend as integer from scraped text; 0 means unknown."""
    if not stipend_str:
        return 0

    raw = str(stipend_str).strip().lower()
    if not raw:
        return 0

    if any(token in raw for token in ["unpaid", "performance based", "performance-based", "negotiable", "depends"]):
        return 0

    cleaned = raw.replace(",", "")
    yearly_markers = ["per annum", "p.a", "/year", "per year", "annum", "yearly", "annual"]
    monthly_markers = ["per month", "/month", "p.m", "pm", "monthly", "month"]
    has_yearly = any(marker in cleaned for marker in yearly_markers)
    has_monthly = any(marker in cleaned for marker in monthly_markers)

    def _to_amount(number: str, suffix: str) -> int:
        value = float(number)
        suffix = (suffix or "").lower()
        if suffix == "k":
            value *= 1_000
        elif suffix in {"l", "lac", "lakh"}:
            value *= 100_000
        return int(value)

    amounts: list[int] = []
    for number, suffix in re.findall(r"(\d+(?:\.\d+)?)\s*(k|l|lac|lakh)?", cleaned):
        amounts.append(_to_amount(number, suffix))

    if not amounts:
        return 0

    monthly_value = min(amounts)
    if monthly_value <= 0:
        return 0

    if has_yearly and not has_monthly:
        monthly_value = int(monthly_value / 12)

    return max(0, monthly_value)


def _raw_stipend(job: dict[str, Any]) -> Any:
    return job.get("stipend") or _as_dict(job.get("raw_data")).get("stipend")


def _hydrate_match_stipends(matches: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    jobs_by_id = {job.get("id"): job for job in jobs}
    for match in matches:
        job = jobs_by_id.get(match.get("job_id"), {})
        stipend = _raw_stipend(job)
        match["stipend"] = stipend
        match["stipend_amount"] = _parse_stipend(stipend)
    return matches


def _apply_stipend_filter(
    matches: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    stipend_min: int,
) -> list[dict[str, Any]]:
    if stipend_min <= 0:
        return matches

    jobs_by_id = {job.get("id"): job for job in jobs}
    filtered: list[dict[str, Any]] = []
    for match in matches:
        job = jobs_by_id.get(match.get("job_id"), {})
        parsed = _parse_stipend(_raw_stipend(job))
        if parsed == 0 or parsed >= stipend_min:
            filtered.append(match)
    return filtered


def _candidate_fallback_score(result_final: float, semantic_similarity: float) -> float:
    """Return a stable non-zero ranking score for near/general recommendations.

    Strict filtering can reject candidates before weighted scoring is computed,
    resulting in 0.0 scores in the UI. This fallback keeps recommendation cards
    useful by leveraging retrieval relevance when needed.
    """
    if result_final > 0:
        return result_final
    # Blend semantic signal into a conservative baseline for warm-up ranking.
    return max(0.02, min(0.55, 0.65 * float(semantic_similarity)))


def _prefilter_jobs_by_preferences(
    jobs: list[dict[str, Any]],
    preferred_roles: list[str],
    preferred_locations: list[str],
    remote_ok: bool,
    hard_limit: int = 350,
) -> list[dict[str, Any]]:
    if not jobs:
        return []

    if not preferred_roles and not preferred_locations:
        return jobs[:hard_limit]

    scored: list[tuple[float, dict[str, Any]]] = []
    for job in jobs:
        title = str(job.get("title") or "")
        location = str(job.get("location") or "")
        location_norm = location.lower()

        role_hit = bool(preferred_roles) and any(
            role_matches_title(role, title) for role in preferred_roles
        )
        location_hit = bool(preferred_locations) and any(
            location_matches(pref, location) for pref in preferred_locations
        )
        remote_hit = remote_ok and ("remote" in location_norm)

        relevance = 0.0
        if role_hit:
            relevance += 2.0
        if location_hit:
            relevance += 1.5
        if remote_hit:
            relevance += 0.5

        if relevance > 0:
            scored.append((relevance, job))

    ranked = [job for _, job in sorted(scored, key=lambda item: item[0], reverse=True)]
    if len(ranked) >= hard_limit:
        return ranked[:hard_limit]

    ranked_ids = {job.get("id") for job in ranked}
    for job in jobs:
        job_id = job.get("id")
        if job_id in ranked_ids:
            continue
        ranked.append(job)
        if len(ranked) >= hard_limit:
            break

    return ranked


def _update_job_scores_in_batches(supabase, updates: list[dict[str, Any]], batch_size: int = 250) -> None:
    global _BULK_SCORE_RPC_AVAILABLE

    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        job_ids = [
            item.get("id")
            for item in batch
            if item.get("id") and item.get("score") is not None
        ]
        scores = [
            float(item.get("score"))
            for item in batch
            if item.get("id") and item.get("score") is not None
        ]
        if not job_ids:
            continue

        if _BULK_SCORE_RPC_AVAILABLE is not False:
            try:
                supabase.rpc(
                    "bulk_update_job_scores",
                    {"p_job_ids": job_ids, "p_scores": scores},
                ).execute()
                _BULK_SCORE_RPC_AVAILABLE = True
                continue
            except Exception as exc:
                _BULK_SCORE_RPC_AVAILABLE = False
                logger.warning("bulk_update_job_scores RPC unavailable; falling back for this batch: %s", exc)

        try:
            # Best-effort fallback in a single request when RPC is unavailable.
            payload = [{"id": job_id, "score": score} for job_id, score in zip(job_ids, scores)]
            supabase.table("jobs").upsert(payload, on_conflict="id").execute()
        except Exception as exc:
            logger.warning("Score batch update fallback failed: %s", exc)


def _save_resume_embedding(supabase, resume_id: str, embedding: list[float]) -> None:
    global _RESUME_EMBEDDING_WARNING_EMITTED

    if not _resume_embedding_column_exists(supabase):
        if not _RESUME_EMBEDDING_WARNING_EMITTED:
            logger.info("resume_embedding column missing; skipping resume embedding cache updates")
            _RESUME_EMBEDDING_WARNING_EMITTED = True
        return

    try:
        (
            supabase.table("resumes")
            .update({"resume_embedding": embedding})
            .eq("id", resume_id)
            .execute()
        )
    except Exception as exc:
        message = str(exc).lower()
        if "column" in message and "resume_embedding" in message and "does not exist" in message:
            _COLUMN_EXISTS_CACHE[("resumes", "resume_embedding")] = False
            if not _RESUME_EMBEDDING_WARNING_EMITTED:
                logger.info("resume_embedding column missing; recomputing embeddings per request")
                _RESUME_EMBEDDING_WARNING_EMITTED = True
            return
        logger.info("Skipping resume embedding cache update: %s", exc)


def _latest_resume_for_user(supabase, user_id: str) -> dict[str, Any] | None:
    # Prefer uploaded_at when available, then created_at, then id as last-resort fallback.
    queries = [
        ("id, extracted_data, resume_embedding, uploaded_at", "uploaded_at"),
        ("id, extracted_data, resume_embedding, created_at", "created_at"),
        ("id, extracted_data, resume_embedding", "id"),
        ("id, extracted_data, uploaded_at", "uploaded_at"),
        ("id, extracted_data, created_at", "created_at"),
        ("id, extracted_data", "id"),
    ]

    for select_clause, order_field in queries:
        try:
            res = (
                supabase.table("resumes")
                .select(select_clause)
                .eq("user_id", user_id)
                .order(order_field, desc=True)
                .limit(1)
                .execute()
            )
            if res.data:
                return res.data[0]
        except Exception:
            continue

    return None


def _location_filter(preferred_locations: list[str]) -> str:
    filters: list[str] = []
    for location in preferred_locations:
        clean = str(location or "").strip().replace(",", " ")
        if clean:
            filters.append(f"location.ilike.%{clean}%")
    return ",".join(filters)


def _execute_jobs_query(supabase, domain: str | None, location_filter: str, limit: int = 500) -> list[dict[str, Any]]:
    query = supabase.table("jobs").select(_JOB_SELECT).eq("is_active", True)
    if domain:
        query = query.eq("job_domain", domain)
    if location_filter:
        query = query.or_(location_filter)
    return (query.limit(limit).execute().data or [])[:limit]


def _fetch_candidate_jobs(
    supabase,
    user_domain: str,
    preferred_locations: list[str],
    limit: int = 600,
) -> list[dict[str, Any]]:
    all_jobs: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()

    def add_jobs(rows: list[dict[str, Any]] | None) -> None:
        for job in rows or []:
            job_id = job.get("id")
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                all_jobs.append(job)

    def base_query():
        return supabase.table("jobs").select(_JOB_SELECT).eq("is_active", True)

    # Step 1: Exact user domain
    if user_domain and user_domain != "general":
        rows = base_query().eq("job_domain", user_domain).limit(200).execute().data or []
        add_jobs(rows)

    # Step 2: Always include general because many crawled jobs get this tag.
    rows = base_query().eq("job_domain", "general").limit(150).execute().data or []
    add_jobs(rows)

    # Step 3: Adjacent domains to avoid over-narrow recall.
    adjacent_domains = {
        "backend": ["frontend", "data", "devops"],
        "frontend": ["backend", "mobile"],
        "ml": ["data", "backend"],
        "data": ["ml", "backend"],
        "devops": ["backend"],
        "mobile": ["frontend"],
        "general": ["backend", "frontend", "ml", "data"],
    }
    adjacent = adjacent_domains.get(user_domain or "general", [])
    for adj_domain in adjacent:
        if len(all_jobs) >= limit:
            break
        rows = base_query().eq("job_domain", adj_domain).limit(100).execute().data or []
        add_jobs(rows)

    # Step 4: Final broad catch-all to guarantee enough candidates.
    if len(all_jobs) < 300:
        rows = base_query().limit(300).execute().data or []
        add_jobs(rows)

    logger.info(
        "Candidate fetch stage: fetched=%s domain=%s preferred_locations=%s",
        len(all_jobs),
        user_domain,
        len(preferred_locations or []),
    )
    return all_jobs[:limit]


@router.get("/debug/stats")
async def match_debug_stats(
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()
    notes: list[str] = []

    total_jobs = 0
    active_jobs = 0
    jobs_by_domain: dict[str, int] = {}
    latest_job_created_at: str | None = None

    try:
        total_jobs = supabase.table("jobs").select("id", count="exact").execute().count or 0
    except Exception as exc:
        notes.append(f"Could not read total jobs: {exc}")

    try:
        active_jobs = (
            supabase.table("jobs")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
            .count
            or 0
        )
    except Exception as exc:
        notes.append(f"Could not read active jobs: {exc}")

    if _column_exists(supabase, "jobs", "job_domain"):
        domain_display = {
            "backend": "Backend",
            "frontend": "Frontend",
            "ml": "ML",
            "data": "Data",
            "devops": "DevOps",
            "mobile": "Mobile",
            "general": "General",
        }
        for raw_domain, label in domain_display.items():
            try:
                count = (
                    supabase.table("jobs")
                    .select("id", count="exact")
                    .eq("is_active", True)
                    .eq("job_domain", raw_domain)
                    .execute()
                    .count
                    or 0
                )
            except Exception:
                count = 0
            jobs_by_domain[label] = count
    else:
        notes.append("job_domain column missing on jobs")

    jobs_by_source: dict[str, int] | None = None
    if _column_exists(supabase, "jobs", "source_name"):
        try:
            source_rows = (
                supabase.table("jobs")
                .select("source_name")
                .eq("is_active", True)
                .limit(5000)
                .execute()
                .data
                or []
            )
            counts: dict[str, int] = {}
            for row in source_rows:
                source = str(row.get("source_name") or "unknown").strip() or "unknown"
                counts[source] = counts.get(source, 0) + 1
            jobs_by_source = counts
        except Exception as exc:
            notes.append(f"Could not read jobs_by_source: {exc}")
    else:
        notes.append("source_name column missing on jobs; jobs_by_source omitted")

    if _column_exists(supabase, "jobs", "created_at"):
        try:
            latest_row = (
                supabase.table("jobs")
                .select("created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
                or []
            )
            latest_job_created_at = latest_row[0].get("created_at") if latest_row else None
        except Exception as exc:
            notes.append(f"Could not read latest_job_created_at: {exc}")
    else:
        notes.append("created_at column missing on jobs")

    resume_embedding_cached = False
    has_resume_embedding_col = _resume_embedding_column_exists(supabase)
    if not has_resume_embedding_col:
        notes.append("resume_embedding column missing; recomputing each request")
    else:
        try:
            resume_row = _latest_resume_for_user(supabase, current_user["id"])
            cached_embedding = (resume_row or {}).get("resume_embedding")
            resume_embedding_cached = isinstance(cached_embedding, list) and len(cached_embedding) > 0
        except Exception as exc:
            notes.append(f"Could not read resume embedding cache status: {exc}")

    preferences_has_stipend_min_column = _column_exists(supabase, "preferences", "stipend_min")
    if not preferences_has_stipend_min_column:
        notes.append("preferences.stipend_min column missing; stipend filter defaults to 0")

    payload: dict[str, Any] = {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "jobs_by_domain": jobs_by_domain,
        "latest_job_created_at": latest_job_created_at,
        "resume_embedding_cached": resume_embedding_cached,
        "preferences_has_stipend_min_column": preferences_has_stipend_min_column,
        "notes": notes,
    }
    if jobs_by_source is not None:
        payload["jobs_by_source"] = jobs_by_source
    return success_response(payload)


@router.get("")
@router.get("/")
async def get_matches(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    t0 = time.perf_counter()
    logger.info("GET /matches started")
    supabase = get_supabase_client()

    resume_row = _latest_resume_for_user(supabase, current_user["id"])
    extracted_data = _as_dict((resume_row or {}).get("extracted_data"))

    pref_select = ["preferred_roles", "preferred_locations", "remote_ok"]
    has_preferred_domains_column = _column_exists(supabase, "preferences", "preferred_domains")
    has_stipend_min_column = _column_exists(supabase, "preferences", "stipend_min")
    if has_preferred_domains_column:
        pref_select.append("preferred_domains")
    if has_stipend_min_column:
        pref_select.append("stipend_min")

    pref_res = (
        supabase.table("preferences")
        .select(",".join(pref_select))
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    preferences = pref_res.data[0] if pref_res.data else {}
    if not has_preferred_domains_column:
        preferences["preferred_domains"] = []

    try:
        stipend_min = max(0, int(preferences.get("stipend_min") or 0)) if has_stipend_min_column else 0
    except (TypeError, ValueError):
        stipend_min = 0

    rejection_reasons: dict[str, int] = {key: 0 for key in _DEBUG_REASON_KEYS}

    if not extracted_data:
        logger.info("Matches computed in %.2fs", time.perf_counter() - t0)
        return success_response(
            {
                "matches": [],
                "meta": {
                    "reason": "resume_not_parsed",
                    "message": "Upload and parse your resume first to generate personalized matches.",
                },
                "debug": {
                    "total_jobs": 0,
                    "retrieved_jobs": 0,
                    "strict_matches": 0,
                    "near_matches": 0,
                    "rejection_reasons": rejection_reasons,
                },
            }
        )

    user_profile = build_user_profile(extracted_data, preferences)
    user_domain = user_profile.domain or "general"
    user_locations = user_profile.preferred_locations or []
    jobs = _fetch_candidate_jobs(
        supabase,
        user_domain,
        user_locations,
        limit=600,
    )
    logger.info("Match stage: candidate_jobs=%s", len(jobs))

    if not jobs:
        logger.info("Matches computed in %.2fs", time.perf_counter() - t0)
        return success_response(
            {
                "matches": [],
                "meta": {
                    "reason": "no_active_jobs",
                    "message": "No active jobs are available right now. Try again after scraper refresh.",
                },
                "debug": {
                    "total_jobs": 0,
                    "retrieved_jobs": 0,
                    "strict_matches": 0,
                    "near_matches": 0,
                    "rejection_reasons": rejection_reasons,
                },
            }
        )

    candidate_jobs = _prefilter_jobs_by_preferences(
        jobs,
        user_profile.preferred_roles,
        user_profile.preferred_locations,
        user_profile.remote_ok,
        hard_limit=380,
    )
    logger.info("Match stage: prefiltered_jobs=%s", len(candidate_jobs))

    behavior_profile = load_behavior_profile(supabase, current_user["id"])
    engine = MatchEngine(user_profile, behavior_profile=behavior_profile)
    retrieval_engine = RetrievalEngine(top_k=300)
    resume_embedding = (resume_row or {}).get("resume_embedding") if _resume_embedding_column_exists(supabase) else None
    if isinstance(resume_embedding, list) and resume_embedding:
        candidates = retrieval_engine.retrieve_with_embeddings(
            resume_embedding,
            candidate_jobs,
            resume_text=user_profile.resume_text,
        )
    else:
        resume_embedding = get_embedding(user_profile.resume_text)
        if resume_embedding and resume_row and resume_row.get("id"):
            background_tasks.add_task(_save_resume_embedding, supabase, resume_row["id"], resume_embedding)
        candidates = retrieval_engine.retrieve_with_embeddings(
            resume_embedding,
            candidate_jobs,
            resume_text=user_profile.resume_text,
        )
    logger.info("Match stage: retrieval_candidates=%s", len(candidates))

    rank_updates: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    near_matches: list[dict[str, Any]] = []
    adaptive_candidates: list[tuple[dict[str, Any], Any, float]] = []
    skill_overlap_sum = 0.0
    semantic_similarity_sum = 0.0

    for candidate in candidates:
        job = candidate.job
        result = engine.evaluate_job(job, semantic_similarity_score=candidate.semantic_similarity)
        skill_overlap_sum += float(result.skill_match_score or 0.0)
        semantic_similarity_sum += float(candidate.semantic_similarity or 0.0)

        if not result.accepted:
            if result.filter_reason in rejection_reasons:
                rejection_reasons[result.filter_reason] += 1
            if result.filter_reason == "below_threshold":
                adaptive_candidates.append((job, result, float(candidate.semantic_similarity or 0.0)))

            fallback_score = _candidate_fallback_score(result.final_score, candidate.semantic_similarity)
            fallback_confidence = result.confidence_level if result.final_score > 0 else "Low"
            fallback_probability = result.selection_probability if result.final_score > 0 else fallback_score
            rejection_reason = result.filter_reason.replace("_", " ") if result.filter_reason else "strict filtering"

            near_matches.append(
                {
                    "job_id": job.get("id"),
                    "title": job.get("title"),
                    "company": (job.get("companies") or {}).get("name"),
                    "location": job.get("location"),
                    "apply_url": job.get("apply_url"),
                    "source_name": job.get("source_name"),
                    "experience_level": job.get("experience_level"),
                    "final_score": round(fallback_score * 100, 2),
                    "score": round(fallback_score * 100, 2),
                    "skill_match_score": round(result.skill_match_score * 100, 2),
                    "project_relevance_score": round(result.project_relevance_score * 100, 2),
                    "experience_depth_score": round(result.experience_depth_score * 100, 2),
                    "semantic_similarity_score": round(candidate.semantic_similarity * 100, 2),
                    "role_match_score": round(result.role_match_score * 100, 2),
                    "location_match_score": round(result.location_match_score * 100, 2),
                    "behavior_score": round(result.behavior_score * 100, 2),
                    "confidence_level": fallback_confidence,
                    "selection_probability": round(fallback_probability * 100, 2),
                    "matched_skills": result.matched_skills,
                    "missing_skills": result.missing_skills,
                    "skill_gaps": result.skill_gaps,
                    "reasons": result.reasons
                    or [f"Near match: filtered by {rejection_reason} during strict ranking."],
                    "penalties": result.penalties,
                    "domain": result.domain,
                    "is_near_match": True,
                }
            )
            continue

        current_score = job.get("score")
        if current_score is None or abs(float(current_score) - result.final_score) > 1e-6:
            rank_updates.append({"id": job.get("id"), "score": result.final_score})

        matches.append(
            {
                "job_id": job.get("id"),
                "title": job.get("title"),
                "company": (job.get("companies") or {}).get("name"),
                "location": job.get("location"),
                "apply_url": job.get("apply_url"),
                "source_name": job.get("source_name"),
                "experience_level": job.get("experience_level"),
                "final_score": round(result.final_score * 100, 2),
                "score": round(result.final_score * 100, 2),
                "skill_match_score": round(result.skill_match_score * 100, 2),
                "project_relevance_score": round(result.project_relevance_score * 100, 2),
                "experience_depth_score": round(result.experience_depth_score * 100, 2),
                "semantic_similarity_score": round(result.semantic_similarity_score * 100, 2),
                "role_match_score": round(result.role_match_score * 100, 2),
                "location_match_score": round(result.location_match_score * 100, 2),
                "behavior_score": round(result.behavior_score * 100, 2),
                "confidence_level": result.confidence_level,
                "selection_probability": round(result.selection_probability * 100, 2),
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills,
                "skill_gaps": result.skill_gaps,
                "reasons": result.reasons,
                "penalties": result.penalties,
                "domain": result.domain,
            }
        )

    if len(matches) < _ADAPTIVE_MIN_STRICT_MATCHES and adaptive_candidates:
        promoted_job_ids: set[str] = set()
        adaptive_candidates.sort(key=lambda item: float(item[1].final_score or 0.0), reverse=True)
        needed = _ADAPTIVE_MIN_STRICT_MATCHES - len(matches)

        for job, result, candidate_semantic in adaptive_candidates:
            if needed <= 0:
                break
            if float(result.final_score or 0.0) < _ADAPTIVE_MINIMUM_SCORE:
                continue

            promoted_job_ids.add(job.get("id"))
            matches.append(
                {
                    "job_id": job.get("id"),
                    "title": job.get("title"),
                    "company": (job.get("companies") or {}).get("name"),
                    "location": job.get("location"),
                    "apply_url": job.get("apply_url"),
                    "source_name": job.get("source_name"),
                    "experience_level": job.get("experience_level"),
                    "final_score": round(result.final_score * 100, 2),
                    "score": round(result.final_score * 100, 2),
                    "skill_match_score": round(result.skill_match_score * 100, 2),
                    "project_relevance_score": round(result.project_relevance_score * 100, 2),
                    "experience_depth_score": round(result.experience_depth_score * 100, 2),
                    "semantic_similarity_score": round(candidate_semantic * 100, 2),
                    "role_match_score": round(result.role_match_score * 100, 2),
                    "location_match_score": round(result.location_match_score * 100, 2),
                    "behavior_score": round(result.behavior_score * 100, 2),
                    "confidence_level": result.confidence_level,
                    "selection_probability": round(result.selection_probability * 100, 2),
                    "matched_skills": result.matched_skills,
                    "missing_skills": result.missing_skills,
                    "skill_gaps": result.skill_gaps,
                    "reasons": (result.reasons or [])
                    + ["Accepted by adaptive threshold (0.38) because strict matches were limited."],
                    "penalties": result.penalties,
                    "domain": result.domain,
                    "is_near_match": False,
                }
            )
            needed -= 1

        if promoted_job_ids:
            near_matches = [item for item in near_matches if item.get("job_id") not in promoted_job_ids]

    if rank_updates:
        background_tasks.add_task(_update_job_scores_in_batches, supabase, rank_updates, 250)

    evaluated_jobs = len(candidates)
    rejection_reason_pct = {
        key: round((value / evaluated_jobs) * 100, 2) if evaluated_jobs else 0.0
        for key, value in rejection_reasons.items()
    }

    debug_payload = {
        "total_jobs": len(jobs),
        "retrieved_jobs": len(candidates),
        "strict_matches": len(matches),
        "near_matches": len(near_matches),
        "rejection_reasons": rejection_reasons,
        "avg_skill_overlap": round((skill_overlap_sum / evaluated_jobs) * 100, 2) if evaluated_jobs else 0.0,
        "avg_semantic_similarity": round((semantic_similarity_sum / evaluated_jobs) * 100, 2)
        if evaluated_jobs
        else 0.0,
        "rejection_reason_pct": rejection_reason_pct,
    }

    if not matches and not near_matches:
        candidate_semantic_by_job_id = {
            candidate.job.get("id"): float(candidate.semantic_similarity)
            for candidate in candidates
            if candidate.job.get("id")
        }

        def _general_rank_value(job: dict[str, Any]) -> float:
            semantic = candidate_semantic_by_job_id.get(job.get("id"), 0.0)
            persisted = float(job.get("score") or 0)
            return max(0.0, 0.70 * semantic + 0.30 * persisted)

        fallback_jobs = sorted(jobs, key=_general_rank_value, reverse=True)
        light_matches = [
            {
                "job_id": job.get("id"),
                "title": job.get("title"),
                "company": (job.get("companies") or {}).get("name"),
                "location": job.get("location"),
                "apply_url": job.get("apply_url"),
                "source_name": job.get("source_name"),
                "experience_level": job.get("experience_level"),
                "final_score": round(_general_rank_value(job) * 100, 2),
                "score": round(_general_rank_value(job) * 100, 2),
                "skill_match_score": 0.0,
                "project_relevance_score": 0.0,
                "experience_depth_score": 0.0,
                "semantic_similarity_score": round(candidate_semantic_by_job_id.get(job.get("id"), 0.0) * 100, 2),
                "role_match_score": 0.0,
                "location_match_score": 0.0,
                "behavior_score": 50.0,
                "confidence_level": "Low",
                "selection_probability": 0.0,
                "matched_skills": [],
                "missing_skills": [],
                "skill_gaps": [],
                "reasons": ["General recommendation while personalized ranking warms up."],
                "penalties": ["Personalized signals were insufficient for strict match scoring."],
                "domain": "general",
                "is_near_match": True,
            }
            for job in fallback_jobs[:100]
        ]
        light_matches = _hydrate_match_stipends(
            _apply_stipend_filter(light_matches, jobs, stipend_min),
            jobs,
        )
        logger.info("Matches computed in %.2fs", time.perf_counter() - t0)
        return success_response(
            {
                "matches": light_matches,
                "meta": {
                    "fallback": True,
                    "message": "Showing general recommendations because no strict or near matches were found.",
                },
                "debug": debug_payload,
            }
        )

    matches = _hydrate_match_stipends(_apply_stipend_filter(matches, jobs, stipend_min), jobs)
    near_matches = _hydrate_match_stipends(_apply_stipend_filter(near_matches, jobs, stipend_min), jobs)
    logger.info(
        "Match stage: strict_after_stipend=%s near_after_stipend=%s",
        len(matches),
        len(near_matches),
    )

    matches.sort(key=lambda item: item["final_score"], reverse=True)
    near_matches.sort(key=lambda item: item["final_score"], reverse=True)

    min_matches_target = 20
    if len(matches) < min_matches_target:
        needed = min_matches_target - len(matches)
        strict_ids = {item.get("job_id") for item in matches}
        padding = [
            nm
            for nm in near_matches
            if nm.get("job_id") not in strict_ids and float(nm.get("final_score") or 0) > 20
        ][:needed]
        for nm in padding:
            nm["is_near_match"] = True
        matches.extend(padding)
        matches.sort(key=lambda item: item["final_score"], reverse=True)

    final_matches = matches[:100]
    total_strict = len([item for item in final_matches if not item.get("is_near_match")])
    total_near = len([item for item in final_matches if item.get("is_near_match")])
    logger.info(
        "Match stage: final_returned=%s strict=%s near=%s",
        len(final_matches),
        total_strict,
        total_near,
    )
    logger.info("Matches computed in %.2fs", time.perf_counter() - t0)
    return success_response(
        {
            "matches": final_matches,
            "meta": {
                "fallback": False,
                "total_strict": total_strict,
                "total_near": total_near,
                "message": None,
            },
            "debug": debug_payload,
        }
    )
