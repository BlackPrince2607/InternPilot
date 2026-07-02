from __future__ import annotations

import asyncio

from bs4 import BeautifulSoup

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
    "co-op",
    "coop",
    "graduate",
    "fresher",
    "junior",
]


class RemotiveFetcher:
    def __init__(self) -> None:
        self.logger = get_logger()

    async def fetch(self) -> list[JobRecord]:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=100"
        jobs: list[JobRecord] = []
        try:
            async with build_httpx_async_client(timeout_seconds=20.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                await asyncio.sleep(0.5)
        except Exception as exc:
            self.logger.warning("Remotive fetch failed: %s", exc)
            return []

        for item in payload.get("jobs", []):
            title = item.get("title") or "Untitled Internship"
            title_lower = title.lower()
            if not any(keyword in title_lower for keyword in INTERNSHIP_KEYWORDS):
                continue
            company_name = normalize_company_name(item.get("company_name") or "Unknown Company")
            apply_url = item.get("url") or ""
            description_html = item.get("description") or ""
            description = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
            tags = item.get("tags") or []
            jobs.append(
                JobRecord(
                    external_id=generate_external_id(title, company_name, apply_url),
                    title=title,
                    company_name=company_name,
                    location=item.get("candidate_required_location") or "Remote",
                    apply_url=apply_url,
                    description=description,
                    posted_at=item.get("publication_date"),
                    source_name="remotive",
                    skills_required=extract_skills(description, tags),
                    source_url=url,
                    raw_data=item,
                )
            )

        self.logger.info("Fetched %s jobs from Remotive", len(jobs))
        return jobs
