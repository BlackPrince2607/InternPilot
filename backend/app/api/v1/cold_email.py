from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client
from app.scraper.db import JobRepository
from app.scraper.utils import get_logger, normalize_company_name
from app.services.email_generator import generate_cold_email
from app.services.user_activity import increment_emails_sent_count

router = APIRouter(prefix="/cold-email", tags=["cold-email"])
logger = get_logger()
MAX_MAILTO_LENGTH = 2000
ALLOWED_TONES = {"professional", "friendly", "confident", "casual"}
_COLUMN_CACHE: dict[tuple[str, str], bool] = {}


def _column_exists(supabase, table_name: str, column_name: str) -> bool:
    key = (table_name, column_name)
    if key in _COLUMN_CACHE:
        return _COLUMN_CACHE[key]
    try:
        supabase.table(table_name).select(column_name).limit(1).execute()
        _COLUMN_CACHE[key] = True
    except Exception as exc:
        message = str(exc).lower()
        _COLUMN_CACHE[key] = not ("column" in message and "does not exist" in message)
    return _COLUMN_CACHE[key]


class GenerateEmailRequest(BaseModel):
    company_name: str
    recipient_email: str = ""
    job_id: str | None = None
    job_title: str | None = None
    job_description: str | None = None
    user_note: str | None = None
    tone: str = "professional"

    @field_validator("tone", mode="before")
    @classmethod
    def validate_tone(cls, value: str) -> str:
        tone = str(value or "professional").strip().lower()
        if tone not in ALLOWED_TONES:
            raise ValueError(f"tone must be one of {sorted(ALLOWED_TONES)}")
        return tone


class RecordSentRequest(BaseModel):
    email_id: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_safe_mailto_url(recipient_email: str, subject: str, body: str) -> tuple[str, str]:
    encoded_subject = quote(subject)
    encoded_body = quote(body)
    base = f"mailto:{recipient_email}?subject={encoded_subject}&body="
    max_body_chars = max(0, MAX_MAILTO_LENGTH - len(base))
    if len(encoded_body) > max_body_chars:
        if max_body_chars > 3:
            body = body[: max(0, max_body_chars // 3 - 3)].rstrip() + "..."
        else:
            body = ""
        encoded_body = quote(body)
    return f"{base}{encoded_body}", body


@router.post("/generate")
async def generate_email(
    payload: GenerateEmailRequest,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()

    resume_res = (
        supabase.table("resumes")
        .select("extracted_data")
        .eq("user_id", current_user["id"])
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    if not resume_res.data:
        raise HTTPException(404, "No parsed resume found")

    resume_data = resume_res.data[0].get("extracted_data") or {}
    if not resume_data:
        raise HTTPException(400, "Latest resume does not contain extracted data")

    job_id = payload.job_id
    job_title = payload.job_title
    job_description = payload.job_description
    company_id = None
    normalized_company_name = normalize_company_name(payload.company_name)

    if job_id:
        job_res = (
            supabase.table("jobs")
            .select("id,title,description,company_id")
            .eq("id", job_id)
            .limit(1)
            .execute()
        )
        if not job_res.data:
            raise HTTPException(404, "Job not found")
        job = job_res.data[0]
        job_title = job_title or job.get("title")
        job_description = job_description or job.get("description")
        company_id = job.get("company_id")

    if not company_id:
        company_res = (
            supabase.table("companies")
            .select("id")
            .eq("name", normalized_company_name)
            .limit(1)
            .execute()
        )
        if company_res.data:
            company_id = company_res.data[0].get("id")
        else:
            company_id = JobRepository(supabase=supabase).get_or_create_company(normalized_company_name)

    if not payload.recipient_email and company_id and _column_exists(supabase, "companies", "contact_emails"):
        company_contact_res = (
            supabase.table("companies")
            .select("contact_emails")
            .eq("id", company_id)
            .limit(1)
            .execute()
        )
        if company_contact_res.data:
            emails = company_contact_res.data[0].get("contact_emails") or []
            if emails:
                payload.recipient_email = emails[0]

    try:
        email = await generate_cold_email(
            resume_data=resume_data,
            company_name=normalized_company_name,
            recipient_email=payload.recipient_email,
            job_title=job_title,
            job_description=job_description,
            user_note=payload.user_note,
            tone=payload.tone,
        )
    except ValueError as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        logger.exception("Cold email generation failed for company=%s job_id=%s: %s", normalized_company_name, job_id, exc)
        raise HTTPException(502, "Failed to generate cold email") from exc

    base_insert = {
        "user_id": current_user["id"],
        "job_id": job_id,
        "company_id": company_id,
        "recipient_email": payload.recipient_email,
        "subject": email["subject"],
        "body": email["body"],
    }
    insert_payloads: list[dict] = []

    if _column_exists(supabase, "cold_emails", "tone"):
        insert_payloads.append({**base_insert, "tone": payload.tone})
    if _column_exists(supabase, "cold_emails", "metadata"):
        insert_payloads.append({**base_insert, "metadata": {"tone": payload.tone}})
    insert_payloads.append(base_insert)

    insert_res = None
    for insert_payload in insert_payloads:
        try:
            insert_res = supabase.table("cold_emails").insert(insert_payload).execute()
            if insert_res.data:
                break
        except Exception:
            continue

    if not insert_res or not insert_res.data:
        raise HTTPException(500, "Failed to store generated email")

    email_id = insert_res.data[0]["id"]
    mailto_url, safe_body = _build_safe_mailto_url(payload.recipient_email, email["subject"], email["body"])
    return success_response(
        {
            "email_id": email_id,
            "subject": email["subject"],
            "body": safe_body,
            "mailto_url": mailto_url,
            "recipient_email": payload.recipient_email,
            "tone": payload.tone,
        }
    )


@router.post("/record-sent")
async def record_sent(
    payload: RecordSentRequest,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()
    email_res = (
        supabase.table("cold_emails")
        .select("id")
        .eq("id", payload.email_id)
        .eq("user_id", current_user["id"])
        .limit(1)
        .execute()
    )
    if not email_res.data:
        raise HTTPException(404, "Email not found")

    (
        supabase.table("cold_emails")
        .update({"sent_at": _now_iso()})
        .eq("id", payload.email_id)
        .eq("user_id", current_user["id"])
        .execute()
    )

    increment_emails_sent_count(current_user["id"])
    return success_response({"recorded": True})


@router.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    result = (
        supabase.table("cold_emails")
        .select("id,subject,body,recipient_email,sent_at,created_at,tone,job_id,companies:company_id(name)")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    history = []
    for item in result.data or []:
        history.append(
            {
                "id": item.get("id"),
                "subject": item.get("subject"),
                "body": item.get("body"),
                "recipient_email": item.get("recipient_email"),
                "company_name": (item.get("companies") or {}).get("name"),
                "sent_at": item.get("sent_at"),
                "created_at": item.get("created_at"),
                "tone": item.get("tone") or "professional",
                "job_id": item.get("job_id"),
            }
        )
    return success_response({"emails": history})
