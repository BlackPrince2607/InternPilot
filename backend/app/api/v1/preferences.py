from fastapi import APIRouter, HTTPException
from supabase import create_client
from pydantic import BaseModel
import os

router = APIRouter(prefix="/preferences", tags=["preferences"])

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class PreferencesModel(BaseModel):
    user_id: str
    preferred_roles: list[str]
    preferred_locations: list[str]
    remote_ok: bool = False

@router.post("/save")
async def save_preferences(prefs: PreferencesModel):
    try:
        # Upsert (insert or update)
        result = supabase.table("preferences").upsert({
            "user_id": prefs.user_id,
            "preferred_roles": prefs.preferred_roles,
            "preferred_locations": prefs.preferred_locations,
            "remote_ok": prefs.remote_ok
        },on_conflict="user_id").execute()

        return {"message": "Preferences saved", "data": result.data}
    except Exception as e:
        raise HTTPException(500, f"Failed: {str(e)}")

@router.get("/{user_id}")
async def get_preferences(user_id: str):
    result = supabase.table("preferences").select("*").eq(
        "user_id", user_id
    ).execute()

    if not result.data:
        return {"preferences": None}

    return {"preferences": result.data[0]}