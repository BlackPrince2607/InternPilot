from __future__ import annotations

from app.dependencies.supabase import get_supabase_client

REQUIRED_TABLE_SELECTS = {
    "companies": "id,name,domain,quality_score",
    "jobs": "id,company_id,external_id,title,score,company_score,recency_score,job_domain,job_embedding",
    "cold_emails": "id,user_id,company_id,recipient_email,subject,body,sent_at",
    "user_activity": "user_id,jobs_applied_count,emails_sent_count,updated_at",
}


def validate_required_schema() -> None:
    supabase = get_supabase_client()
    for table_name, select_clause in REQUIRED_TABLE_SELECTS.items():
        try:
            supabase.table(table_name).select(select_clause).limit(1).execute()
        except Exception as exc:
            raise RuntimeError(f"Required schema validation failed for table '{table_name}': {exc}") from exc
