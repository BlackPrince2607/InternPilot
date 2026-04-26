from __future__ import annotations

import asyncio
import os

from app.scraper.parser import JobRecord
from app.scraper.utils import (
    build_httpx_async_client,
    extract_skills,
    generate_external_id,
    get_logger,
    normalize_company_name,
)


INTERNSHIP_KEYWORDS = [
    "intern",
    "internship",
    "trainee",
    "apprentice",
    "graduate",
    "junior",
    "fresher",
]


class AdzunaFetcher:
    def __init__(self) -> None:
        self.logger = get_logger()
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")

    def _has_credentials(self) -> bool:
        return bool(self.app_id and self.app_key)

    async def fetch(self) -> list[JobRecord]:
        if not self._has_credentials():
            self.logger.warning("Skipping Adzuna: credentials not configured")
            return []

        jobs: list[JobRecord] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for page in range(1, 4):
                url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"
                params = {
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "results_per_page": 50,
                    "what": "software intern OR developer intern OR engineering intern",
                    "where": "India",
                    "content-type": "application/json",
                }
                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except Exception as exc:
                    self.logger.warning("Adzuna page %s failed: %s", page, exc)
                    break

                results = payload.get("results", [])
                if not results:
                    break

                for item in results:
                    title = item.get("title") or "Untitled Internship"
                    title_lower = title.lower()
                    if not any(keyword in title_lower for keyword in INTERNSHIP_KEYWORDS):
                        continue

                    company_name = normalize_company_name(
                        (item.get("company") or {}).get("display_name") or "Unknown Company"
                    )
                    apply_url = item.get("redirect_url") or ""
                    description = item.get("description") or ""
                    jobs.append(
                        JobRecord(
                            external_id=generate_external_id(title, company_name, apply_url),
                            title=title,
                            company_name=company_name,
                            location=(item.get("location") or {}).get("display_name") or "India",
                            apply_url=apply_url,
                            description=description,
                            posted_at=item.get("created"),
                            source_name="adzuna",
                            skills_required=extract_skills(description),
                            source_url=url,
                            raw_data=item,
                        )
                    )

                await asyncio.sleep(1.2)

        self.logger.info("Adzuna returned %s internship jobs", len(jobs))
        return jobs
