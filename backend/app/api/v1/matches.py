from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.auth import get_current_user
from app.dependencies.supabase import get_supabase_client
from app.ranking import compute_job_score
from app.utils.matching import (
    flatten_skills,
    location_matches,
    normalize_skill,
    normalize_terms,
    role_matches_title,
)

router = APIRouter(prefix="/matches", tags=["matches"])


def _as_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}


def _extract_job_skills(job: dict) -> list[str]:
    """
    Pull skills from:
    1) jobs.skills_required
    2) jobs.raw_data fields
    """
    candidates: list[Any] = []

    # 1) direct column
    candidates.append(job.get("skills_required"))

    # 2) raw_data JSONB fallback
    raw_data = _as_dict(job.get("raw_data"))
    for key in ("skills_required", "skills", "required_skills", "technologies", "tech_stack"):
        value = raw_data.get(key)
        if value:
            candidates.append(value)

    # flatten any structured values found
    extracted = []
    for item in candidates:
        extracted.extend(flatten_skills(item))

    if extracted:
        return normalize_terms(extracted)

    return []


def compute_match_score(job: dict, resume_data: dict | None, preferences: dict | None) -> float:
    preferences = preferences or {}

    if not resume_data:
        return 0.5

    user_skills = [normalize_skill(skill) for skill in flatten_skills((resume_data or {}).get("skills"))]
    job_skills = [normalize_skill(skill) for skill in _extract_job_skills(job)]

    if os.getenv("ENV", "development").lower() != "production":
        print("[match-debug] job skills:", job_skills)
        print("[match-debug] user skills:", user_skills)

    if not job_skills or not user_skills:
        base_score = 0.3
    else:
        overlap = set(job_skills) & set(user_skills)
        base_score = len(overlap) / len(job_skills)

    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()

    role_boost = 0.0
    for role in normalize_terms(preferences.get("preferred_roles")):
        if role_matches_title(role, title):
            role_boost = 0.2
            break

    location_boost = 0.0
    for loc in normalize_terms(preferences.get("preferred_locations")):
        if location_matches(loc, location):
            location_boost = 0.1
            break

    match_score = min(base_score + role_boost + location_boost, 1.0)

    if os.getenv("ENV", "development").lower() != "production":
        print("[match-debug] match_score:", match_score)

    return match_score


def _build_why(job: dict, resume_data: dict | None, preferences: dict | None, ranking: dict) -> list[str]:
    why: list[str] = []

    job_skills = flatten_skills(job.get("skills_required"))
    user_skills = flatten_skills((resume_data or {}).get("skills"))
    matched_skills = sorted(set(job_skills) & set(user_skills))

    if matched_skills:
        why.append(f"Matches your {', '.join(matched_skills[:3])} skills")

    for role in normalize_terms((preferences or {}).get("preferred_roles")):
        if role_matches_title(role, (job.get("title") or "").lower()):
            why.append(f"Matches preferred role: {role.title()}")
            break

    for loc in normalize_terms((preferences or {}).get("preferred_locations")):
        if location_matches(loc, (job.get("location") or "").lower()):
            why.append(f"Location matches: {loc.title()}")
            break

    if ranking.get("recency_score", 0) >= 0.8:
        why.append("Recently posted")

    if ranking.get("company_score", 0) >= 0.7:
        why.append("High company quality")

    if not why:
        why.append("Relevant based on your profile")

    return why


def _update_job_scores_in_batches(supabase, updates: list[dict], batch_size: int = 250) -> None:
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        for item in batch:
            job_id = item.get("id")
            if not job_id:
                print(f"Skipping invalid job: {item}")
                continue

            payload = {
                "score": item.get("score"),
                "company_score": item.get("company_score"),
                "recency_score": item.get("recency_score"),
            }

            (
                supabase.table("jobs")
                .update(payload)
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

    resume_data = {
        "skills": extracted_data.get("skills", {}),
        "raw": extracted_data,
    } if resume_row else None

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
        .select("""
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
            company_score,
            recency_score,
            is_active,
            skills_required,
            raw_data,
            companies:company_id(id,name,careers_url,quality_score)
        """)
        .eq("is_active", True)
        .order("score", desc=True)
        .limit(50)
        .execute()
    )
    jobs = jobs_res.data or []

    rank_updates: list[dict] = []
    matches: list[dict] = []

    for job in jobs:
        match_score = compute_match_score(job, resume_data, preferences)
        ranking = compute_job_score(job, match_score, preferences)

        current_score = job.get("score")
        current_company = job.get("company_score")
        current_recency = job.get("recency_score")

        if (
            current_score is None
            or current_company is None
            or current_recency is None
            or abs(float(current_score) - ranking["final_score"]) > 1e-6
            or abs(float(current_company) - ranking["company_score"]) > 1e-6
            or abs(float(current_recency) - ranking["recency_score"]) > 1e-6
        ):
            rank_updates.append({
                "id": job.get("id"),
                "score": ranking["final_score"],
                "company_score": ranking["company_score"],
                "recency_score": ranking["recency_score"],
            })

        why = _build_why(job, resume_data, preferences, ranking)

        matches.append({
            "title": job.get("title"),
            "company": (job.get("companies") or {}).get("name"),
            "location": job.get("location"),
            "score": round(ranking["final_score"] * 100, 2),
            "match_score": round(match_score * 100, 2),
            "company_score": ranking["company_score"],
            "recency_score": ranking["recency_score"],
            "keyword_score": ranking["keyword_score"],
            "apply_url": job.get("apply_url"),
            "why": why,
            "explanation": ", ".join(why),
        })

    if rank_updates:
        background_tasks.add_task(_update_job_scores_in_batches, supabase, rank_updates, 250)

    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches}
