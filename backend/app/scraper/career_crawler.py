from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.dependencies.supabase import get_supabase_client
from app.scraper.utils import build_httpx_async_client, get_logger, infer_company_domain

EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(?:com|in|io|org|net|edu|co|ai|dev|tech|app)\b"
FALSE_POSITIVE_MARKERS = {"example", "domain", "test", "noreply", "no-reply", "support", "info"}
INVALID_EMAIL_MARKERS = {"localhost", "placeholder", "yourcompany", "email.com", "mail.com"}


class CareerCrawler:
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()
        self.logger = get_logger()

    async def crawl_company(self, company_id: str, company_name: str, careers_url: str | None) -> dict:
        resolved_url = careers_url or await self.find_careers_url(company_name)
        emails: list[str] = []

        if resolved_url:
            emails.extend(await self.extract_emails_from_page(resolved_url, company_name=company_name))
            parsed = urlparse(resolved_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            contact_url = urljoin(base_url.rstrip("/") + "/", "contact")
            emails.extend(await self.extract_emails_from_page(contact_url, company_name=company_name))

        deduped_emails = sorted(set(emails))
        payload = {
            "contact_emails": deduped_emails,
            "careers_url": resolved_url,
            "email_crawled_at": datetime.now(timezone.utc).isoformat(),
        }
        self.supabase.table("companies").update(payload).eq("id", company_id).execute()

        result = {
            "company_id": company_id,
            "emails_found": deduped_emails,
            "careers_url": resolved_url,
        }
        self.logger.info("Crawled company %s: %s emails", company_name, len(deduped_emails))
        return result

    async def find_careers_url(self, company_name: str) -> str | None:
        domain = infer_company_domain(company_name)
        if not domain:
            return None

        candidates = [
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://{domain}/work-with-us",
            f"https://careers.{domain}",
        ]

        async with build_httpx_async_client(timeout_seconds=10.0) as client:
            for url in candidates:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return url
                except Exception as exc:
                    self.logger.debug("Career URL probe failed for %s: %s", url, exc)
                await asyncio.sleep(0.5)
        return None

    async def extract_emails_from_page(self, url: str, company_name: str | None = None) -> list[str]:
        try:
            async with build_httpx_async_client(timeout_seconds=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except Exception as exc:
            self.logger.warning("Failed to fetch page %s: %s", url, exc)
            return []

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        emails = set(re.findall(EMAIL_REGEX, html))
        for anchor in soup.select("a[href^='mailto:']"):
            href = anchor.get("href") or ""
            email = href.replace("mailto:", "").split("?", 1)[0].strip()
            if email:
                emails.add(email)

        company_slug = re.sub(r"\s+", "", (company_name or "").lower())
        filtered: list[str] = []
        for email in emails:
            lowered = email.lower()
            domain = lowered.split("@")[-1]
            if any(marker in lowered for marker in INVALID_EMAIL_MARKERS):
                continue
            if any(marker in lowered for marker in FALSE_POSITIVE_MARKERS) and company_slug not in domain:
                continue
            if lowered not in filtered:
                filtered.append(lowered)
        return filtered

    async def crawl_pending_companies(self, limit: int = 20) -> None:
        result = (
            self.supabase.table("companies")
            .select("id,name,careers_url")
            .filter("email_crawled_at", "is", "null")
            .limit(limit)
            .execute()
        )
        tasks = [
            self.crawl_company(
                company_id=company["id"],
                company_name=company.get("name") or "",
                careers_url=company.get("careers_url"),
            )
            for company in (result.data or [])
        ]
        if not tasks:
            self.logger.info("No pending companies to crawl")
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = 0
        failure_count = 0
        for company, crawl_result in zip(result.data or [], results):
            if isinstance(crawl_result, Exception):
                failure_count += 1
                self.logger.error("Failed to crawl company %s: %s", company.get("name"), crawl_result)
                continue
            success_count += 1
            self.logger.info("Career crawl result: %s", crawl_result)

        self.logger.info("Career crawler completed with success=%s failure=%s", success_count, failure_count)
