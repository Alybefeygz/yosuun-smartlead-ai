"""Single-admin authentication boundary for protected lead data."""

from __future__ import annotations

from collections import deque
from functools import wraps
from hashlib import sha256
from hmac import compare_digest
from math import ceil
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from typing import Any, Callable, Deque, Dict, Optional, Tuple, Union

from flask import (
    Blueprint,
    Flask,
    Response,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash


auth = Blueprint("auth", __name__)


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
            self._prune_attempts(client_key, now)
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


def get_csrf_token() -> str:
    """Return a session-bound token for state-changing HTML forms."""

    token = session.get("csrf_token")
    if not isinstance(token, str) or not token:
        token = token_urlsafe(32)
        session["csrf_token"] = token
    return token


def _has_valid_csrf_token() -> bool:
    submitted = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    return (
        isinstance(submitted, str)
        and isinstance(expected, str)
        and bool(submitted)
        and bool(expected)
        and compare_digest(submitted, expected)
    )


def _auth_fingerprint() -> Optional[str]:
    username = current_app.config.get("ADMIN_USERNAME")
    password_hash = current_app.config.get("ADMIN_PASSWORD_HASH")
    if not isinstance(username, str) or not username:
        return None
    if not isinstance(password_hash, str) or not password_hash:
        return None
    return sha256(f"{username}\0{password_hash}".encode("utf-8")).hexdigest()


def _is_admin_authenticated() -> bool:
    expected = _auth_fingerprint()
    actual = session.get("admin_fingerprint")
    return (
        expected is not None
        and isinstance(actual, str)
        and compare_digest(actual, expected)
    )


def admin_page_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Redirect anonymous browser requests to the login page."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not _is_admin_authenticated():
            session.pop("admin_fingerprint", None)
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_api_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Return a stable JSON 401 envelope for anonymous API requests."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not _is_admin_authenticated():
            session.pop("admin_fingerprint", None)
            return (
                jsonify(
                    {
                        "basari": False,
                        "hata": {
                            "kod": "AUTH_REQUIRED",
                            "mesaj": "Bu işlem için yönetici girişi gereklidir.",
                        },
                    }
                ),
                401,
            )
        return view(*args, **kwargs)

    return wrapped


def _client_key() -> str:
    return request.remote_addr or "unknown"


def _login_limiter() -> LoginAttemptLimiter:
    return current_app.extensions["yosuun_login_limiter"]


def _render_login(
    error: Optional[str] = None,
    status_code: int = 200,
) -> Tuple[str, int]:
    return (
        render_template(
            "login.html",
            csrf_token=get_csrf_token(),
            error=error,
        ),
        status_code,
    )


@auth.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, Tuple[str, int]]:
    """Authenticate the configured administrator without exposing credentials."""

    if _is_admin_authenticated():
        return redirect(url_for("main.dashboard"))
    if request.method == "GET":
        return _render_login()

    if not _has_valid_csrf_token():
        return _render_login("Oturum doğrulanamadı. Lütfen tekrar deneyin.", 400)

    limiter = _login_limiter()
    client_key = _client_key()
    retry_after = limiter.retry_after(client_key)
    if retry_after:
        response, status_code = _render_login(
            "Çok fazla başarısız deneme yapıldı. Lütfen daha sonra tekrar deneyin.",
            429,
        )
        flask_response = current_app.make_response((response, status_code))
        flask_response.headers["Retry-After"] = str(retry_after)
        return flask_response

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    configured_username = current_app.config.get("ADMIN_USERNAME")
    configured_password_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    if not isinstance(configured_username, str) or not isinstance(
        configured_password_hash,
        str,
    ):
        current_app.logger.error("Yönetici kimlik bilgileri yapılandırılmamış.")
        return _render_login("Yönetici girişi şu anda kullanılamıyor.", 503)

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

    if not credentials_have_valid_shape or not username_matches or not password_matches:
        limiter.register_failure(client_key)
        current_app.logger.warning("Başarısız yönetici giriş denemesi.")
        return _render_login("Kullanıcı adı veya parola hatalı.", 401)

    fingerprint = _auth_fingerprint()
    if fingerprint is None:
        return _render_login("Yönetici girişi şu anda kullanılamıyor.", 503)

    limiter.clear(client_key)
    session.clear()
    session["admin_fingerprint"] = fingerprint
    session.permanent = True
    get_csrf_token()
    current_app.logger.info("Yönetici oturumu açıldı.")
    return redirect(url_for("main.dashboard"), code=303)


@auth.post("/logout")
@admin_page_required
def logout() -> Response:
    """End the active administrator session through a CSRF-protected POST."""

    if not _has_valid_csrf_token():
        abort(400)
    session.clear()
    return redirect(url_for("auth.login"), code=303)
