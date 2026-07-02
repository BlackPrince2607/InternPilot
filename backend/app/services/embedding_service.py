from __future__ import annotations

import hashlib
import math
from collections import OrderedDict
from functools import lru_cache

_EMBEDDING_CACHE_MAXSIZE = 2000
_EMBEDDING_CACHE: OrderedDict[str, list[float]] = OrderedDict()


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_cached_embedding(key: str) -> list[float] | None:
    cached = _EMBEDDING_CACHE.get(key)
    if cached is not None:
        _EMBEDDING_CACHE.move_to_end(key)
    return cached


def _store_cached_embedding(key: str, vector: list[float]) -> None:
    _EMBEDDING_CACHE[key] = vector
    _EMBEDDING_CACHE.move_to_end(key)
    while len(_EMBEDDING_CACHE) > _EMBEDDING_CACHE_MAXSIZE:
        _EMBEDDING_CACHE.popitem(last=False)


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str) -> list[float]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    key = _cache_key(normalized)
    cached = _get_cached_embedding(key)
    if cached is not None:
        return cached

    model = _get_model()
    vector = model.encode(normalized, normalize_embeddings=True).tolist()
    _store_cached_embedding(key, vector)
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
        cached = _get_cached_embedding(key)
        if cached is not None:
            results[idx] = cached
        else:
            missing_indices.append(idx)
            missing_texts.append(text)

    if missing_texts:
        model = _get_model()
        vectors = model.encode(missing_texts, normalize_embeddings=True).tolist()
        for idx, text, vector in zip(missing_indices, missing_texts, vectors):
            _store_cached_embedding(_cache_key(text), vector)
            results[idx] = vector

    return [vector or [] for vector in results]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    return cosine_similarity_fast(vec_a, vec_b)


def cosine_similarity_fast(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a <= 0 or mag_b <= 0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))
