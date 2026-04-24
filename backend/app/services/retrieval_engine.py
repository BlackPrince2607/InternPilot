from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.embedding_service import cosine_similarity, get_embedding, get_embeddings_batch
from app.services.skill_normalizer import extract_terms_from_text


@dataclass(slots=True)
class RetrievedCandidate:
    job: dict[str, Any]
    semantic_similarity: float


class RetrievalEngine:
    def __init__(self, top_k: int = 200) -> None:
        self.top_k = top_k

    def retrieve(self, resume_text: str, jobs: list[dict[str, Any]]) -> list[RetrievedCandidate]:
        if not jobs:
            return []

        # Fast lexical shortlist first to keep response time predictable.
        lexical_ranked = self._lexical_rank(resume_text, jobs)
        # Keep semantic pass bounded so /matches stays responsive.
        semantic_shortlist_cap = 180
        shortlist_size = min(len(lexical_ranked), min(max(self.top_k * 2, 90), semantic_shortlist_cap))
        shortlist = lexical_ranked[:shortlist_size]
        shortlist_jobs = [item.job for item in shortlist]

        # Try semantic reranking on shortlist; gracefully fall back if model work fails/blocks.
        try:
            resume_embedding = get_embedding(resume_text)
            if not resume_embedding:
                raise ValueError("empty_resume_embedding")

            job_texts = [self._job_text(job) for job in shortlist_jobs]
            job_embeddings = get_embeddings_batch(job_texts)

            candidates = [
                RetrievedCandidate(job=job, semantic_similarity=cosine_similarity(resume_embedding, embedding))
                for job, embedding in zip(shortlist_jobs, job_embeddings)
            ]
            candidates.sort(key=lambda item: item.semantic_similarity, reverse=True)
            return candidates[: self.top_k]
        except Exception:
            # Lexical fallback prevents infinite loading and still respects user/profile text.
            return shortlist[: self.top_k]

    def _lexical_rank(self, resume_text: str, jobs: list[dict[str, Any]]) -> list[RetrievedCandidate]:
        resume_terms = set(extract_terms_from_text(resume_text))
        if not resume_terms:
            return [RetrievedCandidate(job=job, semantic_similarity=0.0) for job in jobs]

        scored: list[RetrievedCandidate] = []
        for job in jobs:
            job_terms = set(extract_terms_from_text(self._job_text(job)))
            if not job_terms:
                score = 0.0
            else:
                overlap = len(resume_terms & job_terms)
                score = overlap / max(1, len(resume_terms | job_terms))
            scored.append(RetrievedCandidate(job=job, semantic_similarity=score))

        scored.sort(key=lambda item: item.semantic_similarity, reverse=True)
        return scored

    @staticmethod
    def _job_text(job: dict[str, Any]) -> str:
        return "\n".join(
            part
            for part in [
                str(job.get("title") or ""),
                str(job.get("description") or ""),
                str(job.get("experience_level") or ""),
            ]
            if part
        )
