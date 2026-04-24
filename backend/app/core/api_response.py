from __future__ import annotations

from typing import Any


def success_response(data: Any = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(message: str) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": message,
    }
