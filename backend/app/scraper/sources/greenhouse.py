from __future__ import annotations

import asyncio

from bs4 import BeautifulSoup

from app.scraper.parser import JobRecord
from app.scraper.utils import build_httpx_async_client, extract_skills, generate_external_id, get_logger


class GreenhouseFetcher:
    def __init__(
        self,
        company_slugs: list[str] | None = None,
    ) -> None:
        self.company_slugs = company_slugs or [
            "razorpay",
            "browserstack",
            "freshworks",
            "cred",
            "meesho",
            "groww",
            "zepto",
            "slice",
        ]
        self.logger = get_logger()

    async def fetch(self) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for slug in self.company_slugs:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                try:
                    response = await client.get(url)
                except Exception as exc:
                    self.logger.warning("Skipping Greenhouse company %s due to request error %s", slug, exc)
                    await asyncio.sleep(0.5)
                    continue
                if response.status_code != 200:
                    self.logger.warning("Skipping Greenhouse company %s due to status %s", slug, response.status_code)
                    await asyncio.sleep(0.5)
                    continue

                payload = response.json()
                company_name = slug.replace("-", " ").title()
                for item in payload.get("jobs", []):
                    title = item.get("title") or "Untitled Internship"
                    apply_url = item.get("absolute_url") or ""
                    description_html = item.get("content") or ""
                    description = BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
                    jobs.append(
                        JobRecord(
                            external_id=generate_external_id(title, company_name, apply_url),
                            title=title,
                            company_name=company_name,
                            location=(item.get("location") or {}).get("name") or "Remote",
                            apply_url=apply_url,
                            description=description,
                            posted_at=item.get("updated_at"),
                            source_name="greenhouse",
                            skills_required=extract_skills(description),
                            source_url=url,
                            raw_data=item,
                        )
                    )
                await asyncio.sleep(0.5)
        return jobs
