from __future__ import annotations

import asyncio
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.scraper.db import JobRepository, PersistenceSummary
from app.scraper.parser import JobRecord
from app.scraper.utils import extract_skills, generate_external_id, get_logger, normalize_location, utc_now_iso
from app.scraper.sources.adzuna import AdzunaFetcher
from app.scraper.sources.greenhouse import GreenhouseFetcher
from app.scraper.sources.lever import LeverFetcher
from app.scraper.sources.remotive import RemotiveFetcher
from app.services.embedding_service import get_embeddings_batch
from app.services.deduplicator import JobDeduplicator
from app.services.job_cleaner import CleanedJob, clean_job_payload, is_low_information_job
from app.services.job_skill_extractor import extract_job_skill_profile
from app.services.skill_normalizer import flatten_skills
from app.services.scrapers.internshala_scraper import InternshalaJobScraper

TECH_DOMAINS = {"backend", "frontend", "ml", "data", "devops", "mobile"}


@dataclass(slots=True)
class PipelineMetrics:
    scraped: int = 0
    stored: int = 0
    rejected: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    persistence: PersistenceSummary | None = None


class JobIngestionPipeline:
    def __init__(self, repository: JobRepository | None = None) -> None:
        self.repository = repository or JobRepository()
        self.logger = get_logger()
        self.deduplicator = JobDeduplicator()
        self.scrapers = [
            InternshalaJobScraper(max_pages=5),
            GreenhouseFetcher(),
            LeverFetcher(),
            RemotiveFetcher(),
        ]
        if os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"):
            self.scrapers.append(AdzunaFetcher())
        else:
            self.logger.info("Adzuna credentials not found — skipping Adzuna scraper")

    async def run(self) -> PipelineMetrics:
        t0 = time.perf_counter()
        metrics = PipelineMetrics()

        async def run_scraper(scraper: Any) -> list[Any]:
            try:
                if hasattr(scraper, "fetch"):
                    return await scraper.fetch()
                if hasattr(scraper, "scrape"):
                    return await scraper.scrape()
                self.logger.warning(
                    "Scraper %s has no fetch() or scrape() method",
                    scraper.__class__.__name__,
                )
                return []
            except Exception as exc:
                self.logger.exception(
                    "Scraper %s failed: %s",
                    scraper.__class__.__name__,
                    exc,
                )
                return []

        results = await asyncio.gather(
            *[run_scraper(scraper) for scraper in self.scrapers],
            return_exceptions=False,
        )

        scraper_stats: dict[str, int] = {}
        for scraper, result in zip(self.scrapers, results):
            name = scraper.__class__.__name__
            count = len(result) if isinstance(result, list) else 0
            scraper_stats[name] = count
            if count == 0:
                self.logger.warning("Scraper stats: %s returned 0 jobs", name)
            else:
                self.logger.info("Scraper stats: %s returned %s jobs", name, count)

        self.logger.info("Full scraper breakdown: %s", scraper_stats)
        if sum(scraper_stats.values()) == 0:
            self.logger.error(
                "CRITICAL: All scrapers returned 0 jobs. Check network connectivity and scraper configs."
            )

        raw_jobs: list[dict] = []
        for scraper, result in zip(self.scrapers, results):
            if not result:
                self.logger.warning("Scraper %s returned 0 jobs", scraper.__class__.__name__)
                continue

            for item in result:
                if hasattr(item, "model_dump"):
                    raw = item.model_dump()
                    raw_jobs.append(
                        {
                            "title": raw.get("title"),
                            "company": raw.get("company_name"),
                            "location": raw.get("location"),
                            "description": raw.get("description"),
                            "skills_required": raw.get("skills_required") or {},
                            "apply_url": raw.get("apply_url"),
                            "posted_at": raw.get("posted_at"),
                            "source": raw.get("source_name"),
                            "raw_data": raw.get("raw_data") or {},
                        }
                    )
                elif isinstance(item, dict):
                    raw_jobs.append(item)

            self.logger.info(
                "Scraper %s returned %s jobs",
                scraper.__class__.__name__,
                len(result),
            )

        metrics.scraped = len(raw_jobs)
        self.logger.info("Total raw jobs across all scrapers: %s", metrics.scraped)

        rejection_counter: Counter[str] = Counter()
        filtered_jobs: list[CleanedJob] = []

        for raw_job in raw_jobs:
            cleaned = clean_job_payload(raw_job)
            if is_low_information_job(cleaned):
                rejection_counter["low_information"] += 1
                continue
            if self.deduplicator.is_duplicate(cleaned.title, cleaned.company, cleaned.location):
                rejection_counter["duplicate"] += 1
                continue
            filtered_jobs.append(cleaned)

        embeddings: list[list[float]] = []
        if filtered_jobs:
            embedding_texts = [f"{job.title}\n{job.description}".strip() for job in filtered_jobs]
            try:
                embeddings = get_embeddings_batch(embedding_texts)
            except Exception as exc:
                self.logger.exception("Batch embedding failed: %s", exc)
                embeddings = [[] for _ in filtered_jobs]

        prepared_jobs: list[JobRecord] = []
        for index, cleaned in enumerate(filtered_jobs):
            embedding = embeddings[index] if index < len(embeddings) else []

            extracted = extract_skills(cleaned.description, cleaned.title)
            normalized_skills = flatten_skills(extracted)
            if len(normalized_skills) < 2:
                rejection_counter["insufficient_skills"] += 1
                continue

            profile = extract_job_skill_profile(
                {
                    "title": cleaned.title,
                    "description": cleaned.description,
                    "skills_required": extracted,
                    "raw_data": cleaned.raw_data,
                }
            )
            if profile.domain not in TECH_DOMAINS:
                rejection_counter["non_technical_domain"] += 1
                continue

            if not embedding:
                rejection_counter["embedding_failed"] += 1
                continue

            raw_payload = {
                **cleaned.raw_data,
                "job_domain": profile.domain,
                "job_embedding": embedding,
                "normalized_skills": normalized_skills,
                "critical_skills": profile.critical_skills,
                "cleaned_description": cleaned.description,
                "pipeline_ingested_at": utc_now_iso(),
            }

            prepared_jobs.append(
                JobRecord(
                    external_id=generate_external_id(cleaned.title, cleaned.company, cleaned.apply_url),
                    title=cleaned.title,
                    company_name=cleaned.company,
                    location=normalize_location(cleaned.location),
                    description=cleaned.description,
                    apply_url=cleaned.apply_url,
                    source_name=cleaned.source,
                    skills_required=extracted,
                    posted_at=cleaned.posted_at,
                    source_url=cleaned.apply_url,
                    raw_data=raw_payload,
                    job_domain=profile.domain,
                    job_embedding=embedding,
                )
            )

        metrics.rejected = sum(rejection_counter.values())
        metrics.rejection_reasons = dict(rejection_counter)

        persistence = self.repository.bulk_insert_jobs(prepared_jobs)
        metrics.stored = persistence.inserted + persistence.updated
        metrics.persistence = persistence

        self.logger.info(
            "Pipeline complete: scraped=%s stored=%s rejected=%s reasons=%s",
            metrics.scraped,
            metrics.stored,
            metrics.rejected,
            metrics.rejection_reasons,
        )
        self.logger.info(
            "JobIngestionPipeline.run() completed in %.2fs scraped=%s stored=%s rejected=%s",
            time.perf_counter() - t0,
            metrics.scraped,
            metrics.stored,
            metrics.rejected,
        )
        return metrics
