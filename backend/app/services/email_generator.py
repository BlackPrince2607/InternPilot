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
    tone: str = "professional",
) -> dict:
    candidate_name = resume_data.get("name") or "The candidate"
    skills = resume_data.get("skills") or {}
    projects = resume_data.get("projects") or []

    tone_instructions = {
        "professional": (
            "Tone: Formal and professional. "
            "Use complete sentences and credible, specific language."
        ),
        "friendly": (
            "Tone: Warm and approachable while staying professional. "
            "Natural wording, no stiff corporate phrases."
        ),
        "confident": (
            "Tone: Assertive and impact-focused. "
            "Highlight outcomes and readiness without sounding arrogant."
        ),
        "casual": (
            "Tone: Friendly and conversational but still respectful. "
            "Sound like a real person, not a template. "
            "Avoid corporate buzzwords."
        ),
    }
    tone_instruction = tone_instructions.get(tone, tone_instructions["professional"])

    prompt = f"""
Write a cold email for an internship application.
{tone_instruction}

Candidate: {candidate_name}
Skills: {json.dumps(skills, ensure_ascii=False)}
Projects: {json.dumps(projects, ensure_ascii=False)}
Company: {company_name}
Role: {job_title or "Software Engineering Intern"}
Job description context: {(job_description or "")[:500]}
Special note from candidate: {user_note or "None"}

Rules:
- Max 220 words
- No "I hope this email finds you well"
- No generic openers
- Reference at least one specific skill or project
- Include a short "Why me" section with 2-3 bullet points tied to resume and role context
- End with a short, specific CTA
- Return JSON with keys: subject, body
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
