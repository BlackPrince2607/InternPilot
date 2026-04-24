from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from app.scraper.db import JobRepository, PersistenceSummary
from app.scraper.parser import JobRecord
from app.scraper.utils import extract_skills, generate_external_id, get_logger, normalize_location, utc_now_iso
from app.services.embedding_service import get_embedding
from app.services.job_cleaner import CleanedJob, clean_job_payload, is_low_information_job
from app.services.job_skill_extractor import extract_job_skill_profile
from app.services.skill_normalizer import flatten_skills
from app.services.deduplicator import JobDeduplicator
from app.services.scrapers.internshala_scraper import InternshalaJobScraper
from app.services.scrapers.linkedin_scraper import LinkedInJobScraper
from app.services.scrapers.wellfound_scraper import WellfoundJobScraper

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
            InternshalaJobScraper(),
            LinkedInJobScraper(),
            WellfoundJobScraper(),
        ]

    async def run(self) -> PipelineMetrics:
        metrics = PipelineMetrics()
        results = await asyncio.gather(*(scraper.scrape() for scraper in self.scrapers), return_exceptions=True)

        raw_jobs: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.exception("Job source failed: %s", result)
                continue
            raw_jobs.extend(result)
        metrics.scraped = len(raw_jobs)

        prepared_jobs: list[JobRecord] = []
        rejection_counter: Counter[str] = Counter()

        for raw_job in raw_jobs:
            cleaned = clean_job_payload(raw_job)
            prepared = self._prepare_job(cleaned)
            if isinstance(prepared, str):
                rejection_counter[prepared] += 1
                continue
            prepared_jobs.append(prepared)

        metrics.rejected = sum(rejection_counter.values())
        metrics.rejection_reasons = dict(rejection_counter)
        persistence = self.repository.bulk_insert_jobs(prepared_jobs)
        metrics.stored = persistence.inserted + persistence.updated
        metrics.persistence = persistence
        return metrics

    def _prepare_job(self, cleaned: CleanedJob) -> JobRecord | str:
        if is_low_information_job(cleaned):
            return "low_information"
        if self.deduplicator.is_duplicate(cleaned.title, cleaned.company, cleaned.location):
            return "duplicate"

        extracted = extract_skills(cleaned.description, cleaned.title)
        normalized_skills = flatten_skills(extracted)
        if len(normalized_skills) < 2:
            return "insufficient_skills"

        profile = extract_job_skill_profile(
            {
                "title": cleaned.title,
                "description": cleaned.description,
                "skills_required": extracted,
                "raw_data": cleaned.raw_data,
            }
        )
        if profile.domain not in TECH_DOMAINS:
            return "non_technical_domain"
        if len(profile.critical_skills) < 2 and len(normalized_skills) < 3:
            return "weak_signal"

        embedding_text = f"{cleaned.title}\n{cleaned.description}".strip()
        embedding = get_embedding(embedding_text)
        if not embedding:
            return "embedding_failed"

        raw_payload = {
            **cleaned.raw_data,
            "job_domain": profile.domain,
            "job_embedding": embedding,
            "normalized_skills": normalized_skills,
            "critical_skills": profile.critical_skills,
            "cleaned_description": cleaned.description,
            "pipeline_ingested_at": utc_now_iso(),
        }

        return JobRecord(
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
