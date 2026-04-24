from __future__ import annotations

from app.scraper.db import JobRepository
from app.scraper.utils import get_logger
from app.services.job_pipeline import JobIngestionPipeline

logger = get_logger()


async def run_job_ingestion_cycle() -> dict:
    pipeline = JobIngestionPipeline(repository=JobRepository())
    metrics = await pipeline.run()
    deactivated = pipeline.repository.deactivate_old_jobs(stale_after_days=30)
    logger.info(
        "Ingestion cycle complete scraped=%s stored=%s rejected=%s deactivated=%s reasons=%s",
        metrics.scraped,
        metrics.stored,
        metrics.rejected,
        deactivated,
        metrics.rejection_reasons,
    )
    return {
        "scraped": metrics.scraped,
        "stored": metrics.stored,
        "rejected": metrics.rejected,
        "deactivated": deactivated,
        "rejection_reasons": metrics.rejection_reasons,
    }
