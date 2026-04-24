import uuid
import os
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client
from app.services.resume_parser import (
    download_pdf,
    extract_text_from_pdf,
    parse_resume_with_llm,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _is_missing_storage_path_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        ("resumes.storage_path" in text and "does not exist" in text)
        or ("'storage_path'" in text and "'resumes'" in text and "schema cache" in text)
        or ("pgrst204" in text and "storage_path" in text and "resumes" in text)
    )


def _get_resume_bucket() -> str:
    return os.getenv("SUPABASE_RESUMES_BUCKET", "resumes")


def _build_resume_file_url(supabase, bucket: str, storage_path: str) -> str:
    """Prefer short-lived signed URL for private buckets, fallback to public URL."""
    try:
        signed = supabase.storage.from_(bucket).create_signed_url(storage_path, 3600)
        signed_url = signed.get("signedURL") if isinstance(signed, dict) else None
        if signed_url:
            return signed_url
    except Exception:
        pass

    return supabase.storage.from_(bucket).get_public_url(storage_path)


def _extract_storage_path_from_url(file_url: str) -> str | None:
    if not file_url:
        return None

    parsed = urlparse(file_url)
    marker = "/storage/v1/object/"
    if marker not in parsed.path:
        return None

    object_path = parsed.path.split(marker, 1)[1]
    if object_path.startswith("public/"):
        object_path = object_path[len("public/"):]
    elif object_path.startswith("sign/"):
        object_path = object_path[len("sign/"):]

    parts = object_path.split("/", 1)
    if len(parts) < 2:
        return None

    return parts[1]


async def _download_resume_bytes(supabase, bucket: str, resume_row: dict) -> bytes:
    storage_path = resume_row.get("storage_path")
    if storage_path:
        return supabase.storage.from_(bucket).download(storage_path)

    file_url = resume_row.get("file_url")
    derived_path = _extract_storage_path_from_url(file_url)
    if derived_path:
        try:
            return supabase.storage.from_(bucket).download(derived_path)
        except Exception:
            pass

    if not file_url:
        raise HTTPException(400, "Resume file URL is missing")

    return await download_pdf(file_url)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload resume PDF to Supabase Storage"""
    user_id = current_user["id"]
    supabase = get_supabase_client()
    bucket = _get_resume_bucket()
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files allowed")
    
    # Read file content
    file_content = await file.read()
    
    # Generate unique filename
    file_name = f"{user_id}/{uuid.uuid4()}.pdf"
    
    try:
        # Upload to Supabase Storage
        supabase.storage.from_(bucket).upload(
            file_name,
            file_content,
            file_options={"content-type": "application/pdf"}
        )
        
        file_url = _build_resume_file_url(supabase, bucket, file_name)
        
        # Save record in database (fallback for schemas that don't have storage_path yet)
        try:
            resume = supabase.table("resumes").insert({
                "user_id": user_id,
                "file_url": file_url,
                "storage_path": file_name,
            }).execute()
        except Exception as exc:
            if not _is_missing_storage_path_error(exc):
                raise

            resume = supabase.table("resumes").insert({
                "user_id": user_id,
                "file_url": file_url,
            }).execute()
        
        return success_response({
            "resume_id": resume.data[0]["id"],
            "file_url": file_url,
            "message": "Resume uploaded successfully"
        })
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
    
@router.post("/parse/{resume_id}")
async def parse_resume(resume_id: str,
                       current_user: dict = Depends(get_current_user)):
    """Parse uploaded resume and extract structured data"""
    user_id = current_user["id"]
    supabase = get_supabase_client()
    bucket = _get_resume_bucket()
    try:
        # 1. Get resume record from database (fallback for schemas without storage_path)
        try:
            resume = supabase.table("resumes").select("id,file_url,storage_path").eq(
                "id", resume_id) \
                .eq("user_id", user_id) \
                .execute()
        except Exception as exc:
            if not _is_missing_storage_path_error(exc):
                raise

            resume = supabase.table("resumes").select("id,file_url").eq(
                "id", resume_id) \
                .eq("user_id", user_id) \
                .execute()
        
        if not resume.data:
            raise HTTPException(404, "Resume not found")
        
        # 2. Download PDF (works for private and public buckets)
        pdf_bytes = await _download_resume_bytes(supabase, bucket, resume.data[0])
        
        # 3. Extract text
        text = extract_text_from_pdf(pdf_bytes)
        if not text or len(text) < 100:
            raise HTTPException(400, "Could not extract text from PDF")
        
        # 4. Parse with LLM
        parsed_data = await parse_resume_with_llm(text)
        
        # 5. Update database with parsed data
        update_res = supabase.table("resumes").update({
            "extracted_data": parsed_data
        }).eq("id", resume_id).eq("user_id", user_id).execute()
        if not update_res.data:
            raise Exception("Update failed")
        
        return success_response({
            "resume_id": resume_id,
            "parsed_data": parsed_data,
            "message": "Resume parsed successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Parsing failed: {str(e)}")

@router.get("/{resume_id}")
async def get_resume(resume_id: str,
                     current_user: dict = Depends(get_current_user)):
    """Get resume data including parsed information"""
    supabase = get_supabase_client()
    
    resume = supabase.table("resumes").select("*") \
        .eq("id", resume_id)\
        .eq("user_id", current_user["id"]) \
        .execute()
    
    if not resume.data:
        raise HTTPException(404, "Resume not found")
    
    return success_response({"resume": resume.data[0]})
