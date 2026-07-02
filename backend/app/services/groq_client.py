from __future__ import annotations

import os

from groq import Groq

_groq_client: Groq | None = None


def get_groq_client() -> Groq:
    global _groq_client

    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _groq_client = Groq(api_key=api_key)
    return _groq_client
