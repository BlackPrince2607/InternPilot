from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import requests

from app.scraper.parser import JobRecord, build_job_record, parse_detail_page, parse_listing_page
from app.scraper.utils import build_retry_session, get_logger, polite_sleep


@dataclass(slots=True)
class ScrapeConfig:
    base_url: str = "https://internshala.com/internships/"
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    include_details: bool = True
    max_pages: int = 3


class InternshalaScraper:
    source_name = "internshala"

    def __init__(
        self,
        config: ScrapeConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or ScrapeConfig()
        self.session = session or build_retry_session()
        self.logger = get_logger()

    def scrape(self) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        for card in self.iter_job_cards():
            detail_data = None
            if self.config.include_details and card.detail_url:
                detail_data = self.fetch_job_detail(str(card.detail_url))
            jobs.append(build_job_record(card, detail_data))
        return jobs

    def iter_job_cards(self) -> Iterator:
        for page_number in range(1, self.config.max_pages + 1):
            page_url = self._build_page_url(page_number)
            polite_sleep(self.config.min_delay_seconds, self.config.max_delay_seconds)
            self.logger.info("Fetching %s page %s: %s", self.source_name, page_number, page_url)
            response = self.session.get(page_url)
            if response.status_code >= 400:
                self.logger.error(
                    "Failed to fetch listing page %s with status %s",
                    page_url,
                    response.status_code,
                )
                continue

            cards = parse_listing_page(response.text, self.config.base_url, page_url)
            self.logger.info("Parsed %s cards from page %s", len(cards), page_number)
            for card in cards:
                yield card

    def fetch_job_detail(self, detail_url: str) -> dict | None:
        polite_sleep(self.config.min_delay_seconds, self.config.max_delay_seconds)
        response = self.session.get(detail_url)
        if response.status_code >= 400:
            self.logger.warning(
                "Skipping detail page %s due to status %s",
                detail_url,
                response.status_code,
            )
            return None

        try:
            return parse_detail_page(response.text)
        except Exception as exc:
            self.logger.exception("Failed to parse detail page %s: %s", detail_url, exc)
            return None

    def _build_page_url(self, page_number: int) -> str:
        if page_number == 1:
            return self.config.base_url
        return f"{self.config.base_url.rstrip('/')}/page-{page_number}/"
