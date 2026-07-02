from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from app.scraper.parser import build_job_record, parse_detail_page, parse_listing_page
from app.scraper.utils import get_logger

DEFAULT_INTERNSHALA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;"
    "q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class InternshalaJobScraper:
    def __init__(self, max_pages: int = 3) -> None:
        self.base_url = "https://internshala.com/internships/"
        self.max_pages = max_pages
        self.logger = get_logger()

    async def scrape(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        async with httpx.AsyncClient(
            headers=DEFAULT_INTERNSHALA_HEADERS,
            timeout=httpx.Timeout(20.0),
            follow_redirects=True,
        ) as client:
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
                        await asyncio.sleep(random.uniform(1.0, 2.5))
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
                await asyncio.sleep(0.8)
        return jobs
