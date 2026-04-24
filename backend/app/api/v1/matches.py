from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client
from app.services.behavior_ranker import load_behavior_profile
from app.services.match_engine import MatchEngine, build_user_profile
from app.services.retrieval_engine import RetrievalEngine
from app.utils.matching import location_matches, role_matches_title

router = APIRouter(prefix="/matches", tags=["matches"])

_DEBUG_REASON_KEYS = (
    "low_skill_overlap",
    "low_semantic_similarity",
    "role_mismatch",
    "location_mismatch",
    "below_threshold",
)

_ADAPTIVE_MINIMUM_SCORE = 0.40
_ADAPTIVE_MIN_STRICT_MATCHES = 8


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
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        for item in batch:
            job_id = item.get("id")
            if not job_id:
                continue
            (
                supabase.table("jobs")
                .update({"score": item.get("score")})
                .eq("id", job_id)
                .execute()
            )


def _latest_resume_for_user(supabase, user_id: str) -> dict[str, Any] | None:
    # Prefer uploaded_at when available, then created_at, then id as last-resort fallback.
    queries = [
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


@router.get("")
@router.get("/")
async def get_matches(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()

    resume_row = _latest_resume_for_user(supabase, current_user["id"])
    extracted_data = _as_dict((resume_row or {}).get("extracted_data"))

    pref_res = (
        supabase.table("preferences")
        .select("preferred_roles,preferred_locations,remote_ok")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    preferences = pref_res.data[0] if pref_res.data else {}

    jobs_res = (
        supabase.table("jobs")
        .select(
            """
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
            score,
            is_active,
            skills_required,
            raw_data,
            companies:company_id(id,name,careers_url,quality_score)
        """
        )
        .eq("is_active", True)
        .limit(700)
        .execute()
    )
    jobs = jobs_res.data or []

    rejection_reasons: dict[str, int] = {key: 0 for key in _DEBUG_REASON_KEYS}

    if not extracted_data:
        return success_response(
            {
                "matches": [],
                "meta": {
                    "reason": "resume_not_parsed",
                    "message": "Upload and parse your resume first to generate personalized matches.",
                },
                "debug": {
                    "total_jobs": len(jobs),
                    "retrieved_jobs": 0,
                    "strict_matches": 0,
                    "near_matches": 0,
                    "rejection_reasons": rejection_reasons,
                },
            }
        )

    if not jobs:
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

    user_profile = build_user_profile(extracted_data, preferences)
    candidate_jobs = _prefilter_jobs_by_preferences(
        jobs,
        user_profile.preferred_roles,
        user_profile.preferred_locations,
        user_profile.remote_ok,
        hard_limit=320,
    )

    behavior_profile = load_behavior_profile(supabase, current_user["id"])
    engine = MatchEngine(user_profile, behavior_profile=behavior_profile)
    retrieval_top_k = min(110, max(50, len(candidate_jobs)))
    retrieval_engine = RetrievalEngine(top_k=retrieval_top_k)
    candidates = retrieval_engine.retrieve(user_profile.resume_text, candidate_jobs)

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
                    + ["Accepted by adaptive threshold (0.45) because strict matches were limited."],
                    "penalties": result.penalties,
                    "domain": result.domain,
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

    if not matches and near_matches:
        near_matches.sort(key=lambda item: item["final_score"], reverse=True)
        return success_response(
            {
                "matches": near_matches[:50],
                "meta": {
                    "fallback": True,
                    "message": "Showing near-matches because strict filters returned no exact matches.",
                },
                "debug": debug_payload,
            }
        )

    if not matches:
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
            }
            for job in fallback_jobs[:50]
        ]
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

    matches.sort(key=lambda item: item["final_score"], reverse=True)
    return success_response({"matches": matches[:50], "meta": {"fallback": False}, "debug": debug_payload})
