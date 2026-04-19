from __future__ import annotations

import argparse
from dotenv import load_dotenv

from app.scraper.db import JobRepository
from app.scraper.internshala import InternshalaScraper, ScrapeConfig
from app.scraper.utils import configure_logging, get_logger, get_missing_env_vars


def run_pipeline(
    source: str,
    max_pages: int,
    include_details: bool,
    min_delay: float,
    max_delay: float,
    batch_size: int,
    dry_run: bool,
) -> int:
    logger = get_logger()
    logger.info(
        "Starting scrape run | source=%s max_pages=%s include_details=%s batch_size=%s dry_run=%s",
        source,
        max_pages,
        include_details,
        batch_size,
        dry_run,
    )

    if source != "internshala":
        raise ValueError(f"Unsupported source: {source}")

    scraper = InternshalaScraper(
        ScrapeConfig(
            max_pages=max_pages,
            include_details=include_details,
            min_delay_seconds=min_delay,
            max_delay_seconds=max_delay,
        )
    )
    jobs = scraper.scrape()
    logger.info("Scrape completed | source=%s jobs_scraped=%s", source, len(jobs))

    if dry_run:
        logger.info("Dry run enabled; skipping Supabase persistence.")
        return 0

    missing_env_vars = get_missing_env_vars()
    if missing_env_vars:
        logger.error("Missing required environment variables: %s", ", ".join(missing_env_vars))
        return 1

    try:
        repository = JobRepository()
        summary = repository.bulk_insert_jobs(jobs, batch_size=batch_size)
        deactivated_count = repository.deactivate_old_jobs(stale_after_days=7)
    except Exception as exc:
        logger.exception("Pipeline run failed | source=%s error=%s", source, exc)
        return 1

    logger.info(
        "Persistence summary | fetched=%s inserted=%s updated=%s skipped=%s deactivated=%s",
        summary.fetched,
        summary.inserted,
        summary.updated,
        summary.skipped,
        deactivated_count,
    )
    logger.info("Finished scrape run | source=%s", source)
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="InternPilot job ingestion runner")
    parser.add_argument("--source", default="internshala")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--include-details", action="store_true")
    parser.add_argument("--min-delay", type=float, default=2.0)
    parser.add_argument("--max-delay", type=float, default=5.0)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    load_dotenv()
    parser = build_arg_parser()
    args = parser.parse_args()
    configure_logging(args.log_level)
    return run_pipeline(
        source=args.source,
        max_pages=args.max_pages,
        include_details=args.include_details,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
