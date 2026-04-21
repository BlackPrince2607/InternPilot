from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scraper.career_crawler import CareerCrawler
from app.scraper.db import JobRepository
from app.scraper.sources.adzuna import AdzunaFetcher
from app.scraper.sources.greenhouse import GreenhouseFetcher
from app.scraper.sources.lever import LeverFetcher
from app.scraper.sources.remotive import RemotiveFetcher
from app.scraper.utils import get_logger

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
        fetchers = []
        for fetcher_cls in (AdzunaFetcher, RemotiveFetcher, GreenhouseFetcher, LeverFetcher):
            try:
                fetchers.append(fetcher_cls())
            except Exception as exc:
                logger.warning("Skipping fetcher %s: %s", fetcher_cls.__name__, exc)

        if not fetchers:
            logger.warning("No scrapers available to run")
            return

        results = await asyncio.gather(*(fetcher.fetch() for fetcher in fetchers), return_exceptions=True)

        all_jobs = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Scraper run failed: %s", result)
                continue
            all_jobs.extend(result)

        repository = JobRepository()
        summary = repository.bulk_insert_jobs(all_jobs)
        deactivated = repository.deactivate_old_jobs(stale_after_days=3)
        logger.info(
            "Scheduler fetched=%s inserted=%s updated=%s skipped=%s deactivated=%s force_run=%s",
            summary.fetched,
            summary.inserted,
            summary.updated,
            summary.skipped,
            deactivated,
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
    first_run_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    _scheduler.add_job(
        run_all_scrapers,
        "interval",
        hours=6,
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
