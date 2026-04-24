from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scraper.career_crawler import CareerCrawler
from app.scraper.utils import get_logger
from app.services.scheduler import run_job_ingestion_cycle

logger = get_logger()
_scheduler: AsyncIOScheduler | None = None
_scheduler_status = {
    "last_run_time": None,
    "last_status": "idle",
    "last_error": None,
    "next_scheduled_run": None,
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _refresh_next_run() -> None:
    if not _scheduler:
        _scheduler_status["next_scheduled_run"] = None
        return
    job = _scheduler.get_job("run_all_scrapers")
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    _scheduler_status["next_scheduled_run"] = next_run


def get_scheduler_status() -> dict:
    _refresh_next_run()
    return dict(_scheduler_status)


async def run_all_scrapers(force_run: bool = False) -> None:
    _scheduler_status["last_run_time"] = _iso_now()
    _scheduler_status["last_status"] = "running"
    _scheduler_status["last_error"] = None
    try:
        summary = await run_job_ingestion_cycle()
        logger.info(
            "Scheduler ingestion summary=%s force_run=%s",
            summary,
            force_run,
        )
        await CareerCrawler().crawl_pending_companies(limit=10)
        _scheduler_status["last_status"] = "success"
    except Exception as exc:
        _scheduler_status["last_status"] = "failure"
        _scheduler_status["last_error"] = str(exc)
        logger.exception("run_all_scrapers failed: %s", exc)
    finally:
        _refresh_next_run()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler()
    interval_hours = max(1, int(os.getenv("SCRAPER_INTERVAL_HOURS", "6")))
    initial_delay_minutes = max(0, int(os.getenv("SCRAPER_INITIAL_DELAY_MINUTES", "10")))
    first_run_at = datetime.now(timezone.utc) + timedelta(minutes=initial_delay_minutes)
    _scheduler.add_job(
        run_all_scrapers,
        "interval",
        hours=interval_hours,
        id="run_all_scrapers",
        replace_existing=True,
        next_run_time=first_run_at,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    _scheduler_status["last_status"] = "scheduled"
    _refresh_next_run()


def stop_scheduler() -> None:
    global _scheduler
    if not _scheduler:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    _scheduler_status["next_scheduled_run"] = None
