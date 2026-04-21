from __future__ import annotations

from app.dependencies.supabase import get_supabase_client


def increment_jobs_applied_count(user_id: str) -> dict:
    supabase = get_supabase_client()
    result = supabase.rpc("increment_jobs_applied", {"target_user_id": user_id}).execute()
    if not result.data:
        return {"jobs_applied_count": 0, "emails_sent_count": 0}
    return result.data[0]


def increment_emails_sent_count(user_id: str) -> dict:
    supabase = get_supabase_client()
    result = supabase.rpc("increment_emails_sent", {"target_user_id": user_id}).execute()
    if not result.data:
        return {"jobs_applied_count": 0, "emails_sent_count": 0}
    return result.data[0]
