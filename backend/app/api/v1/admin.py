from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.v1.auth import get_current_user
from app.core.api_response import success_response
from app.scheduler import get_scheduler_status, run_all_scrapers

router = APIRouter(prefix="/admin", tags=["admin"])
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")


@router.post("/trigger-scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    user_email = current_user.get("email", "")
    if ADMIN_EMAIL and user_email != ADMIN_EMAIL:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    background_tasks.add_task(run_all_scrapers, True)
    return success_response({
        "triggered_by": current_user["id"],
        "status": get_scheduler_status(),
    })


@router.get("/scraper-status")
async def scraper_status(current_user: dict = Depends(get_current_user)):
    return success_response(get_scheduler_status())
