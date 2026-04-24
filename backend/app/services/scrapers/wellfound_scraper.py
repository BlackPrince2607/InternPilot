from __future__ import annotations

import asyncio
from typing import Any

from bs4 import BeautifulSoup

from app.scraper.utils import build_httpx_async_client, get_logger, normalize_whitespace


class WellfoundJobScraper:
    def __init__(self, max_pages: int = 2) -> None:
        self.max_pages = max_pages
        self.logger = get_logger()

    async def scrape(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for page in range(1, self.max_pages + 1):
            url = f"https://wellfound.com/jobs?query=intern&page={page}"
            html = await self._fetch_page_html(url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div[data-test='StartupResult']")
            for card in cards:
                title_node = card.select_one("a[data-test='job-title']")
                company_node = card.select_one("div[data-test='company-name']")
                location_node = card.select_one("div[data-test='job-location']")
                description_node = card.select_one("div[data-test='job-description']")
                if not title_node or not company_node:
                    continue

                jobs.append(
                    {
                        "title": normalize_whitespace(title_node.get_text(" ", strip=True)),
                        "company": normalize_whitespace(company_node.get_text(" ", strip=True)),
                        "location": normalize_whitespace(location_node.get_text(" ", strip=True) if location_node else "Remote"),
                        "description": normalize_whitespace(description_node.get_text(" ", strip=True) if description_node else ""),
                        "skills_required": [],
                        "apply_url": normalize_whitespace(title_node.get("href") or ""),
                        "posted_at": None,
                        "source": "wellfound",
                        "raw_data": {"listing_html": str(card)},
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
            self.logger.info("Wellfound scraper falling back to HTTP for %s: %s", url, exc)

        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                self.logger.warning("Wellfound fetch failed for %s with status %s", url, response.status_code)
                return ""
            return response.text
