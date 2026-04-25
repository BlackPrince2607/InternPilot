from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/preferences", tags=["preferences"])

ALLOWED_DOMAINS = {
    "backend": "Backend",
    "frontend": "Frontend",
    "full stack": "Full Stack",
    "ml/ai": "ML/AI",
    "data science": "Data Science",
    "devops": "DevOps",
    "mobile": "Mobile",
}

class PreferencesModel(BaseModel):
    preferred_roles: list[str]
    preferred_locations: list[str]
    preferred_domains: list[str] = []
    stipend_min: int = 0
    remote_ok: bool = False

    @field_validator("preferred_domains", mode="before")
    @classmethod
    def validate_preferred_domains(cls, value):
        if not value:
            return []
        if not isinstance(value, list):
            value = [value]

        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = str(item or "").strip().lower()
            canonical = ALLOWED_DOMAINS.get(normalized)
            if not canonical or canonical in seen:
                continue
            cleaned.append(canonical)
            seen.add(canonical)
            if len(cleaned) >= 3:
                break
        return cleaned

    @field_validator("stipend_min", mode="before")
    @classmethod
    def validate_stipend_min(cls, value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

@router.post("/save")
async def save_preferences(
    prefs: PreferencesModel,
    current_user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()
    user_id = current_user["id"]
    try:
        # Upsert (insert or update)
        result = supabase.table("preferences").upsert({
            "user_id": user_id,
            "preferred_roles": prefs.preferred_roles,
            "preferred_locations": prefs.preferred_locations,
            "preferred_domains": prefs.preferred_domains,
            "stipend_min": prefs.stipend_min,
            "remote_ok": prefs.remote_ok
        },on_conflict="user_id").execute()

        return success_response({"preferences": result.data[0] if result.data else None})
    except Exception as e:
        raise HTTPException(500, f"Failed: {str(e)}")

@router.get("/me")
async def get_preferences(current_user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    user_id = current_user["id"]
    result = supabase.table("preferences").select("*").eq(
        "user_id", user_id
    ).execute()

    if not result.data:
        return success_response({"preferences": None})

    return success_response({"preferences": result.data[0]})
