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
    "fresher",
    "graduate",
    "entry level",
    "junior",
]


class GreenhouseFetcher:
    def __init__(
        self,
        company_slugs: list[str] | None = None,
    ) -> None:
        self.company_slugs = company_slugs or [
            "razorpay",
            "browserstack",
            "freshworks",
            "meesho",
            "groww",
            "zepto",
            "cred",
            "slice",
            "smallcase",
            "jupiter",
            "niyo",
            "moneytap",
            "dunzo",
            "coinbase",
            "stripe",
            "notion",
            "figma",
            "linear",
            "vercel",
            "supabase",
            "hashicorp",
            "datadog",
            "mongodb",
            "elastic",
            "confluent",
            "cockroachlabs",
            "planetscale",
            "netlify",
            "cloudflare",
            "fastly",
            "postman",
            "gitlab",
            "digitalocean",
            "linode",
            "segment",
            "mixpanel",
            "amplitude",
            "brex",
            "rippling",
            "gusto",
            "lattice",
            "retool",
            "airbyte",
            "dbt-labs",
            "prefect",
            "weights-biases",
            "scale-ai",
            "hugging-face",
            "cohere",
            "anthropic",
            "mistral",
        ]
        self.logger = get_logger()

    async def fetch(self) -> list[JobRecord]:
        jobs: list[JobRecord] = []
        async with build_httpx_async_client(timeout_seconds=20.0) as client:
            for slug in self.company_slugs:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                try:
                    response = await client.get(url)
                    if response.status_code == 404:
                        self.logger.debug("No Greenhouse board for %s (404)", slug)
                        await asyncio.sleep(0.5)
                        continue
                    response.raise_for_status()
                except Exception as exc:
                    self.logger.warning("Skipping Greenhouse slug %s: %s", slug, exc)
                    await asyncio.sleep(0.5)
                    continue

                payload = response.json()
                company_name = normalize_company_name(slug.replace("-", " "))
                for item in payload.get("jobs", []):
                    title = item.get("title") or "Untitled Internship"
                    title_lower = title.lower()
                    if not any(keyword in title_lower for keyword in INTERNSHIP_KEYWORDS):
                        continue
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

            self.logger.info("Greenhouse returned %s internship jobs", len(jobs))
        return jobs
