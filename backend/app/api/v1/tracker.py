from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client
from app.services.user_activity import increment_jobs_applied_count

router = APIRouter(prefix="/tracker", tags=["tracker"])


class RecordApplyRequest(BaseModel):
    job_id: str


@router.post("/record-apply")
async def record_apply(
    payload: RecordApplyRequest,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()

    try:
        supabase.table("user_interactions").insert(
            {
                "user_id": current_user["id"],
                "job_id": payload.job_id,
                "action": "apply",
            }
        ).execute()
    except Exception:
        pass

    counters = increment_jobs_applied_count(current_user["id"])
    return success_response({"jobs_applied_count": counters.get("jobs_applied_count", 0)})


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    result = (
        supabase.table("user_activity")
        .select("jobs_applied_count,emails_sent_count")
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not result.data:
        return success_response({"jobs_applied_count": 0, "emails_sent_count": 0})
    return success_response(result.data[0])
