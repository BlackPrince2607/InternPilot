from fastapi import APIRouter, UploadFile, File, HTTPException
from supabase import create_client
import os
from dotenv import load_dotenv
import uuid
from app.services.resume_parser import (
    download_pdf, 
    extract_text_from_pdf, 
    parse_resume_with_llm
)

load_dotenv()

router = APIRouter(prefix="/resumes", tags=["resumes"])

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = "d4bcad05-870c-4aeb-92b2-4509b0e3f3fe"  # TODO: Get from auth token later
):
    """Upload resume PDF to Supabase Storage"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")
    
    # Read file content
    file_content = await file.read()
    
    # Generate unique filename
    file_name = f"{user_id}/{uuid.uuid4()}.pdf"
    
    try:
        # Upload to Supabase Storage
        supabase.storage.from_("resumes").upload(
            file_name,
            file_content,
            file_options={"content-type": "application/pdf"}
        )
        
        # Get public URL
        file_url = supabase.storage.from_("resumes").get_public_url(file_name)
        
        # Save record in database
        resume = supabase.table("resumes").insert({
            "user_id": user_id,
            "file_url": file_url
        }).execute()
        
        return {
            "resume_id": resume.data[0]["id"],
            "file_url": file_url,
            "message": "Resume uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
    
@router.post("/parse/{resume_id}")
async def parse_resume(resume_id: str):
    """Parse uploaded resume and extract structured data"""
    
    try:
        # 1. Get resume record from database
        resume = supabase.table("resumes").select("*").eq(
            "id", resume_id
        ).execute()
        
        if not resume.data:
            raise HTTPException(404, "Resume not found")
        
        file_url = resume.data[0]["file_url"]
        
        # 2. Download PDF
        pdf_bytes = await download_pdf(file_url)
        
        # 3. Extract text
        text = extract_text_from_pdf(pdf_bytes)
        
        if not text or len(text) < 100:
            raise HTTPException(400, "Could not extract text from PDF")
        
        # 4. Parse with LLM
        parsed_data = await parse_resume_with_llm(text)
        
        # 5. Update database with parsed data
        supabase.table("resumes").update({
            "extracted_data": parsed_data
        }).eq("id", resume_id).execute()
        
        return {
            "resume_id": resume_id,
            "parsed_data": parsed_data,
            "message": "Resume parsed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Parsing failed: {str(e)}")

@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume data including parsed information"""
    
    resume = supabase.table("resumes").select("*").eq(
        "id", resume_id
    ).execute()
    
    if not resume.data:
        raise HTTPException(404, "Resume not found")
    
    return resume.data[0]