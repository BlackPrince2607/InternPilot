from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.v1.auth import get_current_user
from app.scheduler import get_scheduler_status, run_all_scrapers

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/trigger-scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    background_tasks.add_task(run_all_scrapers, True)
    return {
        "success": True,
        "triggered_by": current_user["id"],
        "status": get_scheduler_status(),
    }


@router.get("/scraper-status")
async def scraper_status(current_user: dict = Depends(get_current_user)):
    return get_scheduler_status()
