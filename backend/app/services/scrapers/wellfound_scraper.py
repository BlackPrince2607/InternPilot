from __future__ import annotations

import asyncio
from typing import Any

from bs4 import BeautifulSoup

from app.scraper.utils import build_httpx_async_client, get_logger, normalize_whitespace

BOT_DETECTION_STRINGS = ("unusual traffic", "captcha", "verify you are human")


def _looks_blocked(html: str) -> bool:
    normalized = (html or "").lower()
    return len(html or "") < 500 or any(token in normalized for token in BOT_DETECTION_STRINGS)


class WellfoundJobScraper:
    def __init__(self, max_pages: int = 2) -> None:
        self.max_pages = max_pages
        self.logger = get_logger()

    async def scrape(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        try:
            for page in range(1, self.max_pages + 1):
                url = f"https://wellfound.com/jobs?page={page}&remote=true"
                html = await self._fetch_page_html(url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                cards = soup.select("[data-test='StartupResult'], .styles_component__Ey28k, .job-listing")
                for card in cards:
                    title_node = card.select_one("[data-test='job-title'], h3, h2")
                    company_node = card.select_one("[data-test='StartupResult__name'], [data-test='company-name']")
                    location_node = card.select_one("[data-test='location'], .location")
                    description_node = card.select_one("[data-test='job-description'], p")

                    title = normalize_whitespace(title_node.get_text(" ", strip=True) if title_node else "")
                    company = normalize_whitespace(company_node.get_text(" ", strip=True) if company_node else "")
                    location = normalize_whitespace(location_node.get_text(" ", strip=True) if location_node else "")
                    description = normalize_whitespace(
                        description_node.get_text(" ", strip=True) if description_node else title
                    )
                    if not title or not company:
                        continue

                    jobs.append(
                        {
                            "title": title,
                            "company": company,
                            "location": location or "Remote",
                            "description": description,
                            "skills_required": {},
                            "apply_url": url,
                            "posted_at": None,
                            "source": "wellfound",
                            "raw_data": {"source_url": url},
                        }
                    )
                await asyncio.sleep(1.0)
        finally:
            self.logger.info("Wellfound scraper returned %s jobs", len(jobs))

        return jobs

    async def _fetch_page_html(self, url: str) -> str:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                content = await page.content()
                await browser.close()
                return content
        except Exception as exc:
            self.logger.info("Wellfound Playwright fetch failed; trying httpx fallback: %s", exc)

        try:
            async with build_httpx_async_client(timeout_seconds=20.0) as client:
                response = await client.get(url)
                if response.status_code >= 400:
                    self.logger.warning("Wellfound httpx fallback failed for %s with status %s", url, response.status_code)
                    return ""
                html = response.text
        except Exception as exc:
            self.logger.warning("Wellfound httpx fallback failed for %s: %s", url, exc)
            return ""

        if _looks_blocked(html):
            self.logger.warning("Wellfound scraper failed due to bot detection; httpx fallback returned blocked HTML")
            return ""
        return html
