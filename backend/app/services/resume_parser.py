import pypdf
from groq import Groq
import os
import json
import httpx

async def download_pdf(url: str) -> bytes:
    """Download PDF from URL"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.content

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        from io import BytesIO
        pdf_file = BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")

async def parse_resume_with_llm(text: str) -> dict:
    """Use Groq LLM to extract structured data from resume text"""
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""Extract structured information from this resume.

Resume text:
{text}

Return ONLY a valid JSON object.
Do not include markdown, explanations, or text outside JSON.
Ensure all keys are present exactly as specified.
Structure:
{{
  "name": "Full name",
  "email": "email@example.com",
  "phone": "phone number",
  "college": "College/University name",
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
  "experience": [],
  "github": "github.com/username",
  "linkedin": "linkedin.com/in/username"
}}

If any field is not found, use null or empty array. Extract all technical skills you can find.
"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Low temperature for consistent extraction
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON from LLM:\n{content}")
        return parsed_data
        
    except Exception as e:
        raise Exception(f"LLM parsing failed: {str(e)}")