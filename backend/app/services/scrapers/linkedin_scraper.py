from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

from bs4 import BeautifulSoup

from app.scraper.utils import build_httpx_async_client, get_logger, normalize_whitespace


class LinkedInJobScraper:
    def __init__(self, query: str = "software engineer intern", max_pages: int = 2) -> None:
        self.query = query
        self.max_pages = max_pages
        self.logger = get_logger()

    async def scrape(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for page in range(self.max_pages):
            start = page * 25
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote(self.query)}&location=India&start={start}"
            html = await self._fetch_page_html(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li")
            for card in cards:
                title_node = card.select_one("h3")
                company_node = card.select_one("h4")
                location_node = card.select_one(".job-search-card__location")
                link = card.select_one("a")

                title = normalize_whitespace(title_node.get_text(" ", strip=True) if title_node else "")
                company = normalize_whitespace(company_node.get_text(" ", strip=True) if company_node else "")
                location = normalize_whitespace(location_node.get_text(" ", strip=True) if location_node else "")
                apply_url = normalize_whitespace(link.get("href") if link else "")
                if not (title and company and apply_url):
                    continue

                jobs.append(
                    {
                        "title": title,
                        "company": company,
                        "location": location or "India",
                        "description": "",
                        "skills_required": [],
                        "apply_url": apply_url,
                        "posted_at": None,
                        "source": "linkedin_fallback",
                        "raw_data": {"listing_html": str(card), "query": self.query},
                    }
                )
            await asyncio.sleep(1.0)
        return jobs

    async def _fetch_page_html(self, url: str) -> str:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                content = await page.content()
                await browser.close()
                return content
        except Exception as exc:
            self.logger.info("LinkedIn scraper falling back to HTTP for %s: %s", url, exc)

        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                self.logger.warning("LinkedIn fallback fetch failed for %s with status %s", url, response.status_code)
                return ""
            return response.text
