"""Shared JSON envelope for API error responses."""

from __future__ import annotations

from typing import Tuple

from flask import Response, jsonify


def json_error(code: str, message: str, status_code: int) -> Tuple[Response, int]:
    """Build the safe ``{"basari": false, "hata": {...}}`` error envelope."""

    return (
        jsonify({"basari": False, "hata": {"kod": code, "mesaj": message}}),
        status_code,
    )
