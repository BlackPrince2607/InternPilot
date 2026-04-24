from __future__ import annotations

import base64
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.dependencies.supabase import get_supabase_client

router = APIRouter(prefix="/images", tags=["images"])


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=400)


def _is_missing_generated_images_table(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "public.generated_images" in text and "could not find the table" in text
    ) or "relation 'generated_images' does not exist" in text


def _is_generation_enabled() -> bool:
    return os.getenv("IMAGE_GENERATION_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _placeholder_image_data_uri(prompt: str) -> str:
    safe_prompt = " ".join(prompt.split())[:80]
    escaped = (
        safe_prompt.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='1024' height='1024' viewBox='0 0 1024 1024'>
<defs>
  <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
    <stop offset='0%' stop-color='#0f172a'/>
    <stop offset='100%' stop-color='#1d4ed8'/>
  </linearGradient>
</defs>
<rect width='1024' height='1024' fill='url(#bg)'/>
<circle cx='170' cy='200' r='110' fill='rgba(16,185,129,0.25)'/>
<circle cx='860' cy='790' r='170' fill='rgba(56,189,248,0.22)'/>
<rect x='88' y='690' width='848' height='230' rx='28' fill='rgba(15,23,42,0.62)'/>
<text x='120' y='760' fill='#e2e8f0' font-family='Arial, sans-serif' font-size='34'>InternPilot Image (Placeholder)</text>
<text x='120' y='815' fill='#cbd5e1' font-family='Arial, sans-serif' font-size='27'>Prompt: {escaped}</text>
<text x='120' y='862' fill='#94a3b8' font-family='Arial, sans-serif' font-size='22'>Set IMAGE_PROVIDER_API_KEY to enable a real provider.</text>
</svg>"""

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


@router.post("/generate")
async def generate_image(
    payload: GenerateImageRequest,
    current_user: dict = Depends(get_current_user),
):
    if not _is_generation_enabled():
        raise HTTPException(503, "Image generation is disabled")

    prompt = payload.prompt.strip()
    if len(prompt) < 3:
        raise HTTPException(400, "Prompt must be at least 3 characters")

    provider = os.getenv("IMAGE_PROVIDER", "placeholder").strip() or "placeholder"
    provider_key = os.getenv("IMAGE_PROVIDER_API_KEY", "").strip()

    # Keep provider integration feature-flagged; fallback remains available by default.
    if provider != "placeholder" and not provider_key:
        provider = "placeholder"

    if provider == "placeholder":
        image_url = _placeholder_image_data_uri(prompt)
    else:
        # Future integration hook for real image providers.
        image_url = _placeholder_image_data_uri(prompt)

    supabase = get_supabase_client()
    persisted = True
    try:
        inserted = (
            supabase.table("generated_images")
            .insert(
                {
                    "user_id": current_user["id"],
                    "prompt": prompt,
                    "image_url": image_url,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
    except Exception as exc:
        if not _is_missing_generated_images_table(exc):
            raise HTTPException(500, f"Failed to persist generated image metadata: {str(exc)}") from exc
        inserted = None
        persisted = False

    image_id = inserted.data[0].get("id") if inserted and inserted.data else None
    return success_response(
        {
            "image_id": image_id,
            "prompt": prompt,
            "provider": provider,
            "image_url": image_url,
            "persisted": persisted,
            "base64": image_url.split(",", 1)[1] if image_url.startswith("data:image") else None,
        }
    )
