from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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
    "fresher",
    "graduate",
    "entry level",
    "junior",
]


class LeverFetcher:
    def __init__(
        self,
        company_slugs: list[str] | None = None,
    ) -> None:
        self.company_slugs = company_slugs or [
            "swiggy",
            "dunzo",
            "niyo",
            "moneytap",
            "smallcase",
            "jupiter",
            "fi",
            "kuku-fm",
            "darwinbox",
            "leadsquared",
            "chargebee",
            "hasura",
            "postman",
            "zivy",
            "netflix",
            "twitter",
            "shopify",
            "asana",
            "intercom",
            "zendesk",
            "twilio",
            "plaid",
            "robinhood",
            "carta",
            "chime",
            "nerdwallet",
            "benchling",
            "figma",
            "notion",
            "airtable",
            "zapier",
            "loom",
            "pitch",
        ]
        self.logger = get_logger()

    async def fetch(self) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for slug in self.company_slugs:
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                try:
                    response = await client.get(url)
                    if response.status_code == 404:
                        self.logger.debug("No Lever board for %s (404)", slug)
                        await asyncio.sleep(0.5)
                        continue
                    response.raise_for_status()
                except Exception as exc:
                    self.logger.warning("Skipping Lever company %s due to request error %s", slug, exc)
                    await asyncio.sleep(0.5)
                    continue
                payload = response.json()
                company_name = normalize_company_name(slug.replace("-", " "))
                for item in payload:
                    title = item.get("text") or "Untitled Internship"
                    title_lower = title.lower()
                    if not any(keyword in title_lower for keyword in INTERNSHIP_KEYWORDS):
                        continue
                    apply_url = item.get("hostedUrl") or ""
                    description = item.get("descriptionPlain") or ""
                    created_at = item.get("createdAt")
                    posted_at = None
                    if created_at:
                        posted_at = datetime.fromtimestamp(created_at / 1000, tz=UTC).isoformat()
                    jobs.append(
                        JobRecord(
                            external_id=generate_external_id(title, company_name, apply_url),
                            title=title,
                            company_name=company_name,
                            location=((item.get("categories") or {}).get("location") or "Remote"),
                            apply_url=apply_url,
                            description=description,
                            posted_at=posted_at,
                            source_name="lever",
                            skills_required=extract_skills(description),
                            source_url=url,
                            raw_data=item,
                        )
                    )
                await asyncio.sleep(0.5)

        self.logger.info("Lever returned %s internship jobs", len(jobs))
        return jobs
