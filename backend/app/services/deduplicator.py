from __future__ import annotations

from difflib import SequenceMatcher

from app.scraper.utils import normalize_for_hash


class JobDeduplicator:
    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()

    def key_for(self, title: str, company: str, location: str) -> str:
        return "||".join(
            [
                normalize_for_hash(title),
                normalize_for_hash(company),
                normalize_for_hash(location),
            ]
        )

    def is_duplicate(self, title: str, company: str, location: str) -> bool:
        key = self.key_for(title, company, location)
        if key in self._seen_hashes:
            return True
        self._seen_hashes.add(key)
        return False

    @staticmethod
    def fuzzy_duplicate(title_a: str, title_b: str, threshold: float = 0.92) -> bool:
        return SequenceMatcher(None, title_a.lower(), title_b.lower()).ratio() >= threshold
