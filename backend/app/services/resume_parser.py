import pdfplumber
from groq import Groq
from io import BytesIO
import os
import json
import httpx

# Module-level client — don't reinstantiate on every call
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def download_pdf(url: str) -> bytes:
    """Download PDF from URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.content


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber for better layout handling"""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if text:
                    pages.append(text)

            if not pages:
                raise Exception("No text could be extracted from PDF")

            return "\n\n".join(pages).strip()

    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")


def _normalize_skills(skills) -> dict:
    """Ensure skills dict always has all expected sub-keys"""
    base = {
        "languages": [],
        "frameworks": [],
        "tools": [],
        "databases": []
    }
    if not isinstance(skills, dict):
        return base

    for key in base:
        val = skills.get(key)
        base[key] = val if isinstance(val, list) else []

    return base


def _normalize_parsed_data(data: dict) -> dict:
    """Fill in missing keys with safe defaults after LLM parsing"""
    defaults = {
        "name": None,
        "email": None,
        "phone": None,
        "college": None,
        "graduation_year": None,
        "skills": {},
        "projects": [],
        "experience": [],
        "github": None,
        "linkedin": None
    }

    for key, default in defaults.items():
        if key not in data:
            data[key] = default

    data["skills"] = _normalize_skills(data.get("skills"))

    if not isinstance(data.get("projects"), list):
        data["projects"] = []

    if not isinstance(data.get("experience"), list):
        data["experience"] = []

    return data


async def parse_resume_with_llm(text: str) -> dict:
    """Use Groq LLM to extract structured data from resume text"""

    prompt = f"""Extract structured information from this resume.

Resume text:
{text}

Return ONLY a valid JSON object.
Do not include markdown, explanations, or any text outside the JSON.
Ensure all keys are present exactly as specified below.

IMPORTANT INSTRUCTIONS FOR SKILLS EXTRACTION:
- Extract skills from ALL sections: dedicated skills section, project descriptions, experience bullets, certifications, and anywhere else they appear
- If a technology is mentioned anywhere in the resume (e.g. "built with React", "used PostgreSQL"), include it in the appropriate skills category
- Categorize carefully: languages (Python, Java, C++), frameworks (React, FastAPI, Django), tools (Git, Docker, AWS), databases (PostgreSQL, MongoDB)

Structure to follow exactly:
{{
  "name": "Full name",
  "email": "email@example.com",
  "phone": "phone number or null",
  "college": "College/University name or null",
  "graduation_year": 2027,
  "skills": {{
    "languages": ["Python", "Java"],
    "frameworks": ["FastAPI", "React"],
    "tools": ["Git", "Docker"],
    "databases": ["PostgreSQL", "MongoDB"]
  }},
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["Python", "FastAPI"],
      "highlights": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Role Title",
      "duration": "Jun 2024 - Aug 2024",
      "highlights": ["What you did", "Impact achieved"]
    }}
  ],
  "github": "github.com/username or null",
  "linkedin": "linkedin.com/in/username or null"
}}

If any field is not found in the resume, use null for strings or empty array for lists.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        print("Raw LLM Output:", content)  # Debugging log

        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON from LLM:\n{content}")

        # Normalize to guarantee shape before returning
        return _normalize_parsed_data(parsed_data)

    except Exception as e:
        raise Exception(f"LLM parsing failed: {str(e)}")