from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    supabase = get_supabase_client()
    jobs_res = (
        supabase.table("jobs")
        .select(
            """
            id,
            title,
            location,
            remote_type,
            apply_url,
            source_name,
            experience_level,
            posted_at,
            score,
            is_active,
            skills_required,
            companies:company_id(id,name,careers_url)
        """
        )
        .eq("is_active", True)
        .order("posted_at", desc=True)
        .limit(limit)
        .execute()
    )

    jobs = []
    for item in jobs_res.data or []:
        jobs.append(
            {
                "job_id": item.get("id"),
                "title": item.get("title"),
                "company": (item.get("companies") or {}).get("name"),
                "location": item.get("location"),
                "remote_type": item.get("remote_type"),
                "apply_url": item.get("apply_url"),
                "source_name": item.get("source_name"),
                "experience_level": item.get("experience_level"),
                "posted_at": item.get("posted_at"),
                "score": item.get("score"),
                "skills_required": item.get("skills_required") or {},
            }
        )

    return success_response({"jobs": jobs})
