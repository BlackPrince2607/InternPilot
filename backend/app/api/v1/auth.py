from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def ensure_app_user(current_user: dict) -> None:
    """
    Ensure the authenticated Supabase user also exists in the app's `users` table.
    """
    supabase = get_supabase_client()
    user_id = current_user["id"]

    try:
        supabase.table("users").upsert(
            {
                "id": user_id,
            },
            on_conflict="id",
        ).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to provision app user: {str(exc)}",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate the access token with Supabase and return a normalized user payload.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    token = credentials.credentials
    supabase = get_supabase_client()

    try:
        user_response = supabase.auth.get_user(jwt=token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if not user_response or not user_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = user_response.user
    payload = user.model_dump()
    payload["id"] = user.id
    payload["sub"] = user.id
    ensure_app_user(payload)
    return payload


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user["id"],
            "email": current_user.get("email"),
            "aud": current_user.get("aud"),
            "role": current_user.get("role"),
            "user_metadata": current_user.get("user_metadata", {}),
        }
    }
