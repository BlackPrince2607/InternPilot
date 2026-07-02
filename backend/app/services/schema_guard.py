from __future__ import annotations
import os

from app.dependencies.supabase import get_supabase_client

REQUIRED_TABLE_SELECTS = {
    "users": "id,email,created_at",
    "resumes": "id,user_id,file_url,extracted_data",
    "preferences": "user_id,preferred_roles,preferred_locations,remote_ok,updated_at",
    "companies": "id,name,domain,quality_score",
    "jobs": "id,company_id,external_id,title,score,company_score,recency_score,job_domain,job_embedding",
    "cold_emails": "id,user_id,company_id,recipient_email,subject,body,sent_at",
    "user_activity": "user_id,jobs_applied_count,emails_sent_count,updated_at",
}


def _is_missing_column_error(exc: Exception, table_name: str, column_name: str) -> bool:
    text = str(exc).lower()
    return f"{table_name}.{column_name}" in text and "does not exist" in text


def _is_missing_table_error(exc: Exception, table_name: str) -> bool:
    text = str(exc).lower()
    return (
        f"public.{table_name}" in text and "could not find the table" in text
    ) or (f"relation '{table_name}' does not exist" in text)


def validate_required_schema() -> None:
    supabase = get_supabase_client()

    for table_name, select_clause in REQUIRED_TABLE_SELECTS.items():
        try:
            supabase.table(table_name).select(select_clause).limit(1).execute()
        except Exception as exc:
            raise RuntimeError(f"Required schema validation failed for table '{table_name}': {exc}") from exc

    # Optional compatibility check: if storage_path exists we can use private-bucket-first download,
    # but older schemas should still boot and operate via URL fallback.
    try:
        supabase.table("resumes").select("storage_path").limit(1).execute()
    except Exception as exc:
        if not _is_missing_column_error(exc, "resumes", "storage_path"):
            raise RuntimeError(f"Required schema validation failed for table 'resumes': {exc}") from exc

    # Optional compatibility check for image generation persistence.
    # If absent, API can still generate placeholder images but won't persist metadata.
    try:
        supabase.table("generated_images").select("id").limit(1).execute()
    except Exception as exc:
        if not _is_missing_table_error(exc, "generated_images"):
            raise RuntimeError(f"Required schema validation failed for table 'generated_images': {exc}") from exc

    bucket_name = os.getenv("SUPABASE_RESUMES_BUCKET", "resumes").strip()
    if not bucket_name:
        raise RuntimeError("SUPABASE_RESUMES_BUCKET cannot be empty")

    try:
        buckets = supabase.storage.list_buckets()
    except Exception as exc:
        raise RuntimeError(f"Failed to list Supabase Storage buckets: {exc}") from exc

    bucket_names = {
        (item.get("name") if isinstance(item, dict) else getattr(item, "name", None))
        for item in (buckets or [])
    }
    if bucket_name not in bucket_names:
        raise RuntimeError(
            f"Required Supabase Storage bucket '{bucket_name}' was not found. "
            "Create it or set SUPABASE_RESUMES_BUCKET to an existing bucket name."
        )
