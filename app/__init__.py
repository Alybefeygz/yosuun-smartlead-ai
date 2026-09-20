"""Flask application package and composition root."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Mapping, Optional

from flask import Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from config import resolve_config


def create_app(
    config_name: Optional[str] = None,
    config_overrides: Optional[Mapping[str, Any]] = None,
) -> Flask:
    """Create a Flask application configured for the selected environment."""

    app = Flask(__name__)
    config_class = resolve_config(config_name)
    app.config.from_object(config_class)
    if config_overrides:
        app.config.update(config_overrides)
    if app.config["TRUST_PROXY_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # Imports stay inside the composition root to keep package imports acyclic.
    from app.auth import init_auth
    from app.database import init_db
    from app.routes import init_chat_rate_limit, main

    init_db(app)
    init_auth(app)
    init_chat_rate_limit(app)
    app.register_blueprint(main)

    @app.get("/health")
    def health() -> tuple[Response, int]:
        """Return a cheap process-liveness response."""

        return jsonify({"basari": True, "durum": "aktif"}), 200

    @app.before_request
    def start_request_timer() -> None:
        g.request_started_at = perf_counter()

    @app.after_request
    def log_request_result(response: Response) -> Response:
        started_at = getattr(g, "request_started_at", None)
        duration_ms = (
            round((perf_counter() - started_at) * 1000, 2)
            if started_at is not None
            else None
        )
        app.logger.info(
            "HTTP request tamamlandı. method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "base-uri 'self'; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "script-src 'self'; "
            "style-src 'self'",
        )
        if not app.debug:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        if request.path in {"/login", "/dashboard", "/api/leads"}:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        if not request.path.startswith("/api/"):
            return error

        status_code = error.code or 500
        if status_code == 413:
            error_code = "PAYLOAD_TOO_LARGE"
            message = "İstek gövdesi izin verilen boyutu aşıyor."
        else:
            error_code = "HTTP_ERROR"
            message = "API isteği işlenemedi."
        return (
            jsonify(
                {
                    "basari": False,
                    "hata": {"kod": error_code, "mesaj": message},
                }
            ),
            status_code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        app.logger.exception("Beklenmeyen uygulama hatası.", exc_info=error)
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "basari": False,
                        "hata": {
                            "kod": "INTERNAL_ERROR",
                            "mesaj": "Beklenmeyen bir hata oluştu.",
                        },
                    }
                ),
                500,
            )
        return "Beklenmeyen bir hata oluştu.", 500

    app.logger.info(
        "Yosuun SmartLead uygulaması hazır. config=%s",
        config_class.__name__,
    )
    return app
