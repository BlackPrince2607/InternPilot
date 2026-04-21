from __future__ import annotations

import json

from app.services.resume_parser import get_groq_client
from app.scraper.utils import get_logger

logger = get_logger()


async def generate_cold_email(
    resume_data: dict,
    company_name: str,
    recipient_email: str,
    job_title: str | None = None,
    job_description: str | None = None,
    user_note: str | None = None,
) -> dict:
    candidate_name = resume_data.get("name") or "The candidate"
    skills = resume_data.get("skills") or {}
    projects = resume_data.get("projects") or []

    prompt = f"""
Write a concise professional cold email for an internship application.

Candidate name: {candidate_name}
Candidate skills: {json.dumps(skills, ensure_ascii=False)}
Candidate projects: {json.dumps(projects, ensure_ascii=False)}
Company name: {company_name}
Recipient email: {recipient_email}
Job title: {job_title or ""}
Job description: {job_description or ""}
User note: {user_note or ""}

Requirements:
- Max 200 words
- No fluff
- Do not use generic phrases like "I hope this email finds you well"
- Personalize it to the company and role when details are available
- Return JSON with exactly these keys: subject, body
"""

    logger.info("Generating cold email for company=%s job_title=%s", company_name, job_title or "")

    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        logger.info("Cold email raw output preview: %s", content[:200])
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.exception("Cold email generation returned invalid JSON for %s: %s", company_name, exc)
        raise ValueError("Cold email generation returned invalid JSON") from exc
    except Exception as exc:
        logger.exception("Cold email generation failed for %s: %s", company_name, exc)
        raise

    return {
        "subject": parsed.get("subject", "").strip(),
        "body": parsed.get("body", "").strip(),
    }
