from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.v1.auth import get_current_user
from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/preferences", tags=["preferences"])

class PreferencesModel(BaseModel):
    preferred_roles: list[str]
    preferred_locations: list[str]
    remote_ok: bool = False

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
            "remote_ok": prefs.remote_ok
        },on_conflict="user_id").execute()

        return {"message": "Preferences saved", "data": result.data}
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
        return {"preferences": None}

    return {"preferences": result.data[0]}
