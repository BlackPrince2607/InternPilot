from __future__ import annotations

import asyncio
import os
from datetime import date

from app.scraper.parser import JobRecord
from app.scraper.utils import (
    build_httpx_async_client,
    extract_skills,
    generate_external_id,
    get_logger,
    normalize_company_name,
)


class AdzunaFetcher:
    _last_reset_date: date | None = None
    _runs_today: int = 0

    def __init__(self) -> None:
        self.logger = get_logger()
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.max_daily_runs = max(1, int(os.getenv("ADZUNA_MAX_DAILY_RUNS", "8")))

    def _has_credentials(self) -> bool:
        return bool(self.app_id and self.app_key)

    @classmethod
    def _register_run(cls) -> bool:
        today = date.today()
        if cls._last_reset_date != today:
            cls._last_reset_date = today
            cls._runs_today = 0
        if cls._runs_today >=  cls._get_limit():
            return False
        cls._runs_today += 1
        return True

    @classmethod
    def _get_limit(cls) -> int:
        return max(1, int(os.getenv("ADZUNA_MAX_DAILY_RUNS", "8")))

    async def fetch(self) -> list[JobRecord]:
        if not self._has_credentials():
            self.logger.warning("Skipping Adzuna fetch: ADZUNA_APP_ID or ADZUNA_APP_KEY is missing")
            return []

        if not self._register_run():
            self.logger.warning("Skipping Adzuna fetch: daily run limit reached")
            return []

        jobs: list[JobRecord] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for page in range(1, 6):
                url = f"https://api.adzuna.com/v1/api/jobs/in/search/{page}"
                params = {
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "results_per_page": 50,
                    "what": "intern OR internship",
                    "where": "India",
                    "content-type": "application/json",
                }
                try:
                    self.logger.info("Fetching Adzuna page %s", page)
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                except Exception as exc:
                    self.logger.exception("Failed to fetch Adzuna page %s: %s", page, exc)
                    await asyncio.sleep(1)
                    continue

                for item in payload.get("results", []):
                    title = item.get("title") or "Untitled Internship"
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

                await asyncio.sleep(1)
        return jobs
