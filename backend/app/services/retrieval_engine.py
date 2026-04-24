from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.embedding_service import cosine_similarity, get_embedding, get_embeddings_batch


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

        resume_embedding = get_embedding(resume_text)
        job_texts = [self._job_text(job) for job in jobs]
        job_embeddings = get_embeddings_batch(job_texts)

        candidates = [
            RetrievedCandidate(job=job, semantic_similarity=cosine_similarity(resume_embedding, embedding))
            for job, embedding in zip(jobs, job_embeddings)
        ]
        candidates.sort(key=lambda item: item.semantic_similarity, reverse=True)
        return candidates[: self.top_k]

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
