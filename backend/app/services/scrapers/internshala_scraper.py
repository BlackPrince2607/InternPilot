from __future__ import annotations

import asyncio
from typing import Any

from app.scraper.parser import build_job_record, parse_detail_page, parse_listing_page
from app.scraper.utils import build_httpx_async_client, get_logger


class InternshalaJobScraper:
    def __init__(self, max_pages: int = 3) -> None:
        self.base_url = "https://internshala.com/internships/"
        self.max_pages = max_pages
        self.logger = get_logger()

    async def scrape(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for page_number in range(1, self.max_pages + 1):
                page_url = self.base_url if page_number == 1 else f"{self.base_url.rstrip('/')}/page-{page_number}/"
                response = await client.get(page_url)
                if response.status_code >= 400:
                    self.logger.warning("Internshala listing fetch failed for %s with status %s", page_url, response.status_code)
                    continue

                cards = parse_listing_page(response.text, self.base_url, page_url)
                for card in cards:
                    detail_data = None
                    if card.detail_url:
                        detail_response = await client.get(str(card.detail_url))
                        if detail_response.status_code < 400:
                            detail_data = parse_detail_page(detail_response.text)
                    record = build_job_record(card, detail_data)
                    jobs.append(
                        {
                            "title": record.title,
                            "company": record.company_name,
                            "location": record.location,
                            "description": record.description,
                            "skills_required": record.skills_required,
                            "apply_url": record.apply_url,
                            "posted_at": record.posted_at,
                            "source": "internshala",
                            "raw_data": record.raw_data,
                        }
                    )
                await asyncio.sleep(1.0)
        return jobs
