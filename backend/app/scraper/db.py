from __future__ import annotations

from dataclasses import dataclass

from supabase import Client

from app.dependencies.supabase import get_supabase_client
from app.scraper.parser import JobRecord
from app.scraper.utils import (
    get_company_score,
    get_logger,
    normalize_company_name,
    utc_days_ago_iso,
)


@dataclass(slots=True)
class PersistenceSummary:
    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0


class JobRepository:
    def __init__(self, supabase: Client | None = None) -> None:
        self.supabase = supabase or get_supabase_client()
        self.logger = get_logger()
        self._company_cache: dict[str, str] = {}

    def get_existing_job_external_ids(self, external_ids: list[str]) -> set[str]:
        if not external_ids:
            return set()

        result = (
            self.supabase.table("jobs")
            .select("external_id")
            .in_("external_id", external_ids)
            .execute()
        )
        return {row["external_id"] for row in result.data or [] if row.get("external_id")}

    def get_or_create_company(self, company_name: str) -> str:
        normalized_name = normalize_company_name(company_name)
        quality_score = get_company_score(normalized_name)
        if normalized_name in self._company_cache:
            return self._company_cache[normalized_name]

        existing = (
            self.supabase.table("companies")
            .select("id,name,quality_score")
            .eq("name", normalized_name)
            .limit(1)
            .execute()
        )
        if existing.data:
            company_id = existing.data[0]["id"]
            existing_score = existing.data[0].get("quality_score") or 0
            if quality_score > existing_score:
                (
                    self.supabase.table("companies")
                    .update({"quality_score": quality_score})
                    .eq("id", company_id)
                    .execute()
                )
            self._company_cache[normalized_name] = company_id
            return company_id

        created = (
            self.supabase.table("companies")
            .insert({"name": normalized_name, "quality_score": quality_score})
            .execute()
        )
        if not created.data:
            raise RuntimeError(f"Failed to create company row for {normalized_name}")

        company_id = created.data[0]["id"]
        self._company_cache[normalized_name] = company_id
        return company_id

    def insert_job(self, job: JobRecord) -> dict:
        company_id = self.get_or_create_company(job.company_name)
        payload = {
            "company_id": company_id,
            "external_id": job.external_id,
            "title": job.title,
            "location": job.location,
            "description": job.description,
            "apply_url": str(job.apply_url),
            "source_name": job.source_name,
            "skills_required": job.skills_required,
            "experience_level": job.experience_level,
            "is_active": job.is_active,
            "posted_at": job.posted_at,
            "last_seen_at": job.last_seen_at,
            "source_url": job.source_url,
            "raw_data": job.raw_data,
        }
        result = self.supabase.table("jobs").upsert(payload, on_conflict="external_id").execute()
        if not result.data:
            raise RuntimeError(f"Failed to upsert job {job.external_id}")
        return result.data[0]

    def bulk_insert_jobs(self, jobs: list[JobRecord], batch_size: int = 50) -> PersistenceSummary:
        summary = PersistenceSummary(fetched=len(jobs))
        if not jobs:
            return summary

        unique_jobs: dict[str, JobRecord] = {}
        for job in jobs:
            unique_jobs[job.external_id] = job
        deduped_jobs = list(unique_jobs.values())
        summary.skipped += len(jobs) - len(deduped_jobs)

        existing_ids = self.get_existing_job_external_ids([job.external_id for job in deduped_jobs])
        summary.updated = len(existing_ids)

        for start in range(0, len(deduped_jobs), batch_size):
            batch = deduped_jobs[start : start + batch_size]
            payload: list[dict] = []
            for job in batch:
                try:
                    company_id = self.get_or_create_company(job.company_name)
                    payload.append(
                        {
                            "company_id": company_id,
                            "external_id": job.external_id,
                            "title": job.title,
                            "location": job.location,
                            "description": job.description,
                            "apply_url": str(job.apply_url),
                            "source_name": job.source_name,
                            "skills_required": job.skills_required,
                            "experience_level": job.experience_level,
                            "is_active": job.is_active,
                            "posted_at": job.posted_at,
                            "last_seen_at": job.last_seen_at,
                            "source_url": job.source_url,
                            "raw_data": job.raw_data,
                        }
                    )
                except Exception as exc:
                    summary.skipped += 1
                    self.logger.exception("Skipping broken job %s: %s", job.external_id, exc)

            if not payload:
                continue

            self.supabase.table("jobs").upsert(payload, on_conflict="external_id").execute()
            inserted_now = sum(1 for item in payload if item["external_id"] not in existing_ids)
            summary.inserted += inserted_now

        return summary

    def deactivate_old_jobs(self, stale_after_days: int = 7) -> int:
        cutoff = utc_days_ago_iso(stale_after_days)
        try:
            result = self.supabase.rpc(
                "deactivate_old_jobs",
                {"cutoff_timestamp": cutoff},
            ).execute()
            if isinstance(result.data, int):
                return result.data
        except Exception as exc:
            self.logger.warning("RPC deactivate_old_jobs unavailable, falling back to update query: %s", exc)

        result = (
            self.supabase.table("jobs")
            .update({"is_active": False})
            .eq("is_active", True)
            .lt("last_seen_at", cutoff)
            .execute()
        )
        return len(result.data or [])
