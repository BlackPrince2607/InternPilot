from __future__ import annotations

import hashlib
import math
from functools import lru_cache

_EMBEDDING_CACHE: dict[str, list[float]] = {}


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> list[float]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    key = _cache_key(normalized)
    cached = _EMBEDDING_CACHE.get(key)
    if cached is not None:
        return cached

    model = _get_model()
    vector = model.encode(normalized, normalize_embeddings=True).tolist()
    _EMBEDDING_CACHE[key] = vector
    return vector


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    normalized = [(text or "").strip() for text in texts]
    results: list[list[float] | None] = [None] * len(normalized)
    missing_indices: list[int] = []
    missing_texts: list[str] = []

    for idx, text in enumerate(normalized):
        if not text:
            results[idx] = []
            continue
        key = _cache_key(text)
        cached = _EMBEDDING_CACHE.get(key)
        if cached is not None:
            results[idx] = cached
        else:
            missing_indices.append(idx)
            missing_texts.append(text)

    if missing_texts:
        model = _get_model()
        vectors = model.encode(missing_texts, normalize_embeddings=True).tolist()
        for idx, text, vector in zip(missing_indices, missing_texts, vectors):
            _EMBEDDING_CACHE[_cache_key(text)] = vector
            results[idx] = vector

    return [vector or [] for vector in results]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a <= 0 or mag_b <= 0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))
