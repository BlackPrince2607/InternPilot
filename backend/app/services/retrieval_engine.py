from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.embedding_service import cosine_similarity_fast, get_embedding
from app.services.skill_normalizer import extract_terms_from_text


@dataclass(slots=True)
class RetrievedCandidate:
    job: dict[str, Any]
    semantic_similarity: float


class RetrievalEngine:
    def __init__(self, top_k: int = 200) -> None:
        self.top_k = top_k
        self.min_similarity = 0.35

    def retrieve(self, resume_text: str, jobs: list[dict[str, Any]]) -> list[RetrievedCandidate]:
        return self.retrieve_with_stored_embeddings(resume_text, jobs)

    def retrieve_with_stored_embeddings(
        self, resume_text: str, jobs: list[dict[str, Any]]
    ) -> list[RetrievedCandidate]:
        resume_embedding = get_embedding(resume_text)
        return self.retrieve_with_embeddings(resume_embedding, jobs, resume_text=resume_text)

    def retrieve_with_embeddings(
        self,
        resume_embedding: list[float],
        jobs: list[dict[str, Any]],
        resume_text: str = "",
    ) -> list[RetrievedCandidate]:
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
            if not resume_embedding:
                raise ValueError("empty_resume_embedding")

            candidates: list[RetrievedCandidate] = []
            for job in shortlist_jobs:
                job_embedding = job.get("job_embedding")
                if not isinstance(job_embedding, list):
                    job_embedding = get_embedding(self._job_text(job))
                candidates.append(
                    RetrievedCandidate(
                        job=job,
                        semantic_similarity=cosine_similarity_fast(resume_embedding, job_embedding),
                    )
                )
            candidates.sort(key=lambda item: item.semantic_similarity, reverse=True)
            candidates = [
                candidate for candidate in candidates if candidate.semantic_similarity >= self.min_similarity
            ]
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
