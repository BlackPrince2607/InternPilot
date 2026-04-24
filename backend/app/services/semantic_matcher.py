from __future__ import annotations

from difflib import SequenceMatcher


def semantic_similarity(resume_text: str, job_text: str) -> float:
    if not resume_text or not job_text:
        return 0.0
    return SequenceMatcher(None, resume_text.lower(), job_text.lower()).ratio()
