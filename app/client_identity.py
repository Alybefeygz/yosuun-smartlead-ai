"""Decide which client a request belongs to for rate limiting.

Requests from the Wix backend all share Wix's server IP, so the Wix site
forwards a per-visitor ID together with a shared secret. The visitor ID is
trusted only when the secret matches; every other request is keyed by IP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from hmac import compare_digest

from flask import current_app, request


WIX_SECRET_HEADER = "X-Wix-Secret"
CLIENT_ID_HEADER = "X-Client-Id"
_CLIENT_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{16,64}")

# Wix requests without a usable visitor ID share one bucket, as before.
WIX_ANONYMOUS_KEY = "wix:anonim"


@dataclass(frozen=True)
class ClientIdentity:
    """Rate-limit identity of the current request."""

    key: str
    via_wix: bool


def resolve_client_identity() -> ClientIdentity:
    """Return the per-visitor identity for Wix requests, otherwise the IP."""

    if not _has_valid_wix_secret():
        return ClientIdentity(key=f"ip:{request.remote_addr or 'unknown'}", via_wix=False)

    client_id = request.headers.get(CLIENT_ID_HEADER, "")
    if _CLIENT_ID_PATTERN.fullmatch(client_id):
        return ClientIdentity(key=f"wix:{client_id}", via_wix=True)
    return ClientIdentity(key=WIX_ANONYMOUS_KEY, via_wix=True)


def _has_valid_wix_secret() -> bool:
    expected = current_app.config.get("WIX_SHARED_SECRET")
    if not isinstance(expected, str) or not expected:
        return False
    submitted = request.headers.get(WIX_SECRET_HEADER, "")
    return compare_digest(submitted.encode("utf-8"), expected.encode("utf-8"))
