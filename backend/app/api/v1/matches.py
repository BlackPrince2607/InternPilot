from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.auth import get_current_user
from app.dependencies.supabase import get_supabase_client
from app.services.behavior_ranker import load_behavior_profile
from app.services.match_engine import MatchEngine, build_user_profile
from app.services.retrieval_engine import RetrievalEngine

router = APIRouter(prefix="/matches", tags=["matches"])


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


@router.get("/")
async def get_matches(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()

    resume_res = (
        supabase.table("resumes")
        .select("id, extracted_data, uploaded_at")
        .eq("user_id", current_user["id"])
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    resume_row = resume_res.data[0] if resume_res.data else None
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
        .limit(1000)
        .execute()
    )
    jobs = jobs_res.data or []

    if not extracted_data:
        return {"matches": []}

    user_profile = build_user_profile(extracted_data, preferences)
    behavior_profile = load_behavior_profile(supabase, current_user["id"])
    engine = MatchEngine(user_profile, behavior_profile=behavior_profile)
    retrieval_engine = RetrievalEngine(top_k=200)
    candidates = retrieval_engine.retrieve(user_profile.resume_text, jobs)

    rank_updates: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []

    for candidate in candidates:
        job = candidate.job
        result = engine.evaluate_job(job, semantic_similarity_score=candidate.semantic_similarity)
        if not result.accepted:
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
                "why": result.reasons,
                "reasons": result.reasons,
                "penalties": result.penalties,
                "domain": result.domain,
            }
        )

    if rank_updates:
        background_tasks.add_task(_update_job_scores_in_batches, supabase, rank_updates, 250)

    matches.sort(key=lambda item: item["final_score"], reverse=True)
    return {"matches": matches[:50]}
