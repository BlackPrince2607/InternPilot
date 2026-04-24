from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag
from pydantic import BaseModel, Field

from app.scraper.utils import (
    extract_skills,
    generate_external_id,
    normalize_company_name,
    normalize_location,
    normalize_whitespace,
    utc_now_iso,
)


class JobCard(BaseModel):
    title: str
    company_name: str
    location: str
    apply_url: str
    source_url: str
    detail_url: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


class JobRecord(BaseModel):
    external_id: str
    title: str
    company_name: str
    location: str
    description: str = ""
    apply_url: str
    source_name: str = "internshala"
    skills_required: dict = Field(default_factory=dict)
    experience_level: str | None = None
    posted_at: str | None = None
    last_seen_at: str = Field(default_factory=utc_now_iso)
    is_active: bool = True
    stipend: str | None = None
    source_url: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    job_domain: str | None = None
    job_embedding: list[float] | None = None


def safe_select(element: Tag, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = element.select_one(selector)
        if not node:
            continue
        text = normalize_whitespace(node.get_text(" ", strip=True))
        if text:
            return text
    return None


def safe_select_attr(element: Tag, selectors: list[str], attribute: str) -> str | None:
    for selector in selectors:
        node = element.select_one(selector)
        if not node:
            continue
        value = normalize_whitespace(node.get(attribute))
        if value:
            return value
    return None


def safe_select_all(element: Tag, selectors: list[str]) -> list[str]:
    values: list[str] = []
    for selector in selectors:
        nodes = element.select(selector)
        for node in nodes:
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if text and text not in values:
                values.append(text)
        if values:
            return values
    return values


def parse_listing_page(html: str, base_url: str, source_url: str) -> list[JobCard]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.individual_internship, div.internship_meta, div[data-internship-id]")

    parsed_cards: list[JobCard] = []
    for card in cards:
        title = safe_select(
            card,
            [
                "a.job-title-href",
                "a.job-title",
                "h3 a",
                "a[href*='/internship/detail/']",
                "a[href*='/internship/']",
            ],
        ) or ""
        company_name = normalize_company_name(
            safe_select(
                card,
                [
                    "p.company-name",
                    "a.company-name",
                    "div.company_name",
                    "h4.company-name",
                    ".company",
                ],
            )
            or ""
        )
        locations = [
            normalize_location(location)
            for location in safe_select_all(
                card,
                [
                    "a.location_link",
                    "span.location_link",
                    "div.locations span",
                    ".row-1-item.locations span",
                    ".locations",
                ],
            )
            if location
        ]
        location = normalize_location(", ".join(dict.fromkeys(locations))) if locations else "Remote"
        href = safe_select_attr(
            card,
            [
                "a.job-title-href",
                "a.job-title",
                "a[href*='/internship/detail/']",
                "a[href*='/internship/']",
            ],
            "href",
        ) or ""
        apply_url = urljoin(base_url, href)

        if not (title and company_name and apply_url):
            continue

        parsed_cards.append(
            JobCard(
                title=title,
                company_name=company_name,
                location=location,
                apply_url=apply_url,
                source_url=source_url,
                detail_url=apply_url,
                raw_data={
                    "listing_html": str(card),
                    "source_url": source_url,
                },
            )
        )

    return parsed_cards


def parse_detail_page(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    description_selectors = [
        "div.text-container",
        "div.internship_details",
        "div.internship-description",
        "div.detail_view",
        "div#details",
    ]
    description_parts: list[str] = []
    for selector in description_selectors:
        node = soup.select_one(selector)
        if node:
            description_parts.append(node.get_text("\n", strip=True))
            break

    skill_tags = soup.select(
        "span.round_tabs, div.round_tabs, .skills span, .skill_names span, a.round_tabs"
    )
    skills = [normalize_whitespace(tag.get_text(" ", strip=True)) for tag in skill_tags]
    stipend_tag = soup.select_one(
        "span.stipend, div.stipend, span.salary, div.salary, span.item_body, div.item_body"
    )
    experience_tag = soup.select_one("div.experience, span.experience")

    description = normalize_whitespace("\n".join(part for part in description_parts if part))
    extracted_skills = extract_skills(description, skills)

    return {
        "description": description,
        "skills_required": extracted_skills,
        "stipend": normalize_whitespace(stipend_tag.get_text(" ", strip=True) if stipend_tag else ""),
        "experience_level": normalize_whitespace(
            experience_tag.get_text(" ", strip=True) if experience_tag else ""
        )
        or None,
        "raw_html": html,
    }


def build_job_record(card: JobCard, detail_data: dict[str, Any] | None = None) -> JobRecord:
    detail_data = detail_data or {}
    description = normalize_whitespace(detail_data.get("description", ""))
    skills_required = detail_data.get("skills_required") or extract_skills(card.title)

    return JobRecord(
        external_id=generate_external_id(card.title, card.company_name, str(card.apply_url)),
        title=normalize_whitespace(card.title),
        company_name=normalize_company_name(card.company_name),
        location=normalize_location(card.location),
        description=description,
        apply_url=str(card.apply_url),
        source_name="internshala",
        skills_required=skills_required,
        experience_level=detail_data.get("experience_level"),
        stipend=detail_data.get("stipend") or None,
        source_url=card.source_url,
        raw_data={
            "listing": card.raw_data,
            "detail": detail_data,
            "card": card.model_dump(mode="json"),
        },
    )
