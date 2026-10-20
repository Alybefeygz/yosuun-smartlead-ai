"""Single-admin bearer-token authentication for protected lead data."""

from __future__ import annotations

from collections import deque
from functools import wraps
from hashlib import sha256
from hmac import compare_digest
from math import ceil
from threading import Lock
from time import monotonic
from typing import Any, Callable, Deque, Dict, Optional, Tuple

from flask import Blueprint, Flask, Response, current_app, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash

from app.client_identity import resolve_client_identity
from app.responses import json_error


auth = Blueprint("auth", __name__)

# Separates admin API tokens from any other value signed with SECRET_KEY.
ADMIN_TOKEN_SALT = "yosuun-admin-token"

CREDENTIALS_OK = "ok"
CREDENTIALS_INVALID = "invalid"
CREDENTIALS_UNAVAILABLE = "unavailable"


class LoginAttemptLimiter:
    """Bound repeated login failures by client address for one app process."""

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        lockout_seconds: int,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: Dict[str, Deque[float]] = {}
        self._blocked_until: Dict[str, float] = {}
        self._lock = Lock()

    def retry_after(self, client_key: str) -> int:
        """Return remaining lockout seconds, or zero when login is allowed."""

        now = monotonic()
        with self._lock:
            blocked_until = self._blocked_until.get(client_key, 0.0)
            if blocked_until > now:
                return max(1, ceil(blocked_until - now))
            self._blocked_until.pop(client_key, None)
            self._prune_attempts(client_key, now)
        return 0

    def register_failure(self, client_key: str) -> None:
        """Record one failure and start a lockout at the configured threshold."""

        now = monotonic()
        with self._lock:
            self._prune_all(now)
            attempts = self._attempts.setdefault(client_key, deque())
            attempts.append(now)
            if len(attempts) >= self.max_attempts:
                self._blocked_until[client_key] = now + self.lockout_seconds
                self._attempts.pop(client_key, None)

    def clear(self, client_key: str) -> None:
        """Clear failures after a successful login."""

        with self._lock:
            self._attempts.pop(client_key, None)
            self._blocked_until.pop(client_key, None)

    def _prune_all(self, now: float) -> None:
        """Forget expired lockouts and idle clients so memory stays bounded."""

        for client_key in list(self._attempts):
            self._prune_attempts(client_key, now)
        for client_key, blocked_until in list(self._blocked_until.items()):
            if blocked_until <= now:
                del self._blocked_until[client_key]

    def _prune_attempts(self, client_key: str, now: float) -> None:
        attempts = self._attempts.get(client_key)
        if attempts is None:
            return
        cutoff = now - self.window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if not attempts:
            self._attempts.pop(client_key, None)


def init_auth(app: Flask) -> None:
    """Register authentication routes and process-local login throttling."""

    app.extensions["yosuun_login_limiter"] = LoginAttemptLimiter(
        max_attempts=app.config["AUTH_MAX_ATTEMPTS"],
        window_seconds=app.config["AUTH_ATTEMPT_WINDOW_SECONDS"],
        lockout_seconds=app.config["AUTH_LOCKOUT_SECONDS"],
    )
    app.register_blueprint(auth)


def _auth_fingerprint() -> Optional[str]:
    username = current_app.config.get("ADMIN_USERNAME")
    password_hash = current_app.config.get("ADMIN_PASSWORD_HASH")
    if not isinstance(username, str) or not username:
        return None
    if not isinstance(password_hash, str) or not password_hash:
        return None
    return sha256(f"{username}\0{password_hash}".encode("utf-8")).hexdigest()


def _token_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.secret_key, salt=ADMIN_TOKEN_SALT)


def _token_max_age_seconds() -> int:
    return current_app.config["ADMIN_TOKEN_MAX_AGE_SECONDS"]


def _has_valid_bearer_token() -> bool:
    """Accept a signed, unexpired token bound to the current admin credentials."""

    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        return False

    expected = _auth_fingerprint()
    if expected is None:
        return False

    try:
        payload = _token_serializer().loads(token, max_age=_token_max_age_seconds())
    except BadSignature:
        return False

    actual = payload.get("fp") if isinstance(payload, dict) else None
    return isinstance(actual, str) and compare_digest(actual, expected)


def admin_api_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Return a stable JSON 401 envelope for requests without a valid token."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if _has_valid_bearer_token():
            return view(*args, **kwargs)
        return json_error(
            "AUTH_REQUIRED",
            "Bu işlem için yönetici girişi gereklidir.",
            401,
        )

    return wrapped


def _login_limiter() -> LoginAttemptLimiter:
    return current_app.extensions["yosuun_login_limiter"]


def _check_credentials(username: str, password: str) -> str:
    """Compare submitted credentials with the configured admin in constant time."""

    configured_username = current_app.config.get("ADMIN_USERNAME")
    configured_password_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    if not isinstance(configured_username, str) or not isinstance(
        configured_password_hash,
        str,
    ):
        current_app.logger.error("Yönetici kimlik bilgileri yapılandırılmamış.")
        return CREDENTIALS_UNAVAILABLE

    credentials_have_valid_shape = (
        bool(username)
        and len(username) <= 100
        and bool(password)
        and len(password) <= 256
    )
    username_matches = compare_digest(
        username.encode("utf-8"),
        configured_username.encode("utf-8"),
    )
    try:
        password_matches = check_password_hash(
            configured_password_hash,
            password if len(password) <= 256 else "",
        )
    except (AttributeError, TypeError, ValueError):
        current_app.logger.error("Yönetici parola hash'i geçersiz.")
        password_matches = False

    if credentials_have_valid_shape and username_matches and password_matches:
        return CREDENTIALS_OK
    return CREDENTIALS_INVALID


@auth.post("/api/admin/token")
def admin_token() -> Tuple[Response, int]:
    """Exchange admin credentials for a short-lived bearer token.

    The Wix backend cannot carry a cookie session between calls, so it
    authenticates lead listing requests with this token instead.
    """

    limiter = _login_limiter()
    client_key = resolve_client_identity().key
    retry_after = limiter.retry_after(client_key)
    if retry_after:
        response, status_code = json_error(
            "RATE_LIMITED",
            "Çok fazla başarısız deneme yapıldı. Lütfen daha sonra tekrar deneyin.",
            429,
        )
        response.headers["Retry-After"] = str(retry_after)
        return response, status_code

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return json_error(
            "VALIDATION_ERROR",
            "JSON istek gövdesi bir nesne olmalıdır.",
            400,
        )

    username = payload.get("kullanici_adi")
    password = payload.get("parola")
    status = _check_credentials(
        username.strip() if isinstance(username, str) else "",
        password if isinstance(password, str) else "",
    )
    if status == CREDENTIALS_UNAVAILABLE:
        return json_error(
            "AUTH_UNAVAILABLE",
            "Yönetici girişi şu anda kullanılamıyor.",
            503,
        )
    if status == CREDENTIALS_INVALID:
        limiter.register_failure(client_key)
        current_app.logger.warning("Başarısız yönetici token denemesi.")
        return json_error(
            "AUTH_FAILED",
            "Kullanıcı adı veya parola hatalı.",
            401,
        )

    fingerprint = _auth_fingerprint()
    if fingerprint is None:
        return json_error(
            "AUTH_UNAVAILABLE",
            "Yönetici girişi şu anda kullanılamıyor.",
            503,
        )

    limiter.clear(client_key)
    current_app.logger.info("Yönetici API token'ı oluşturuldu.")
    return (
        jsonify(
            {
                "basari": True,
                "token": _token_serializer().dumps({"fp": fingerprint}),
                "sure_saniye": _token_max_age_seconds(),
            }
        ),
        200,
    )
