"""HTTP adapter for visitor chat, lead capture and lead listing."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from app.auth import admin_api_required, admin_page_required, get_csrf_token
from app.database import lead_ekle, tum_leadler
from app.services.ai_service import AIServiceError, ai_service
from app.services.rate_limiter import SlidingWindowRateLimiter


main = Blueprint("main", __name__)

NAME_MAX_LENGTH = 100
PHONE_MAX_LENGTH = 50
LEAD_MESSAGE_MAX_LENGTH = 2000
CHAT_MESSAGE_MAX_LENGTH = 4000
HISTORY_MESSAGE_MAX_LENGTH = 4000
ALLOWED_HISTORY_ROLES = frozenset({"user", "assistant"})


class RequestValidationError(ValueError):
    """Raised when an HTTP request violates the public API contract."""


def init_chat_rate_limit(app) -> None:
    """Attach process-local abuse protection for the public chat endpoint."""

    app.extensions["yosuun_chat_limiter"] = SlidingWindowRateLimiter(
        max_requests=app.config["CHAT_RATE_LIMIT_REQUESTS"],
        window_seconds=app.config["CHAT_RATE_LIMIT_WINDOW_SECONDS"],
    )


def _chat_retry_after() -> int:
    limiter = current_app.extensions["yosuun_chat_limiter"]
    client_key = request.remote_addr or "unknown"
    return limiter.acquire(client_key)


def _error_response(
    code: str,
    message: str,
    status_code: int,
) -> Tuple[Response, int]:
    """Build the shared safe API error envelope."""

    return (
        jsonify(
            {
                "basari": False,
                "hata": {
                    "kod": code,
                    "mesaj": message,
                },
            }
        ),
        status_code,
    )


def _json_object() -> Dict[str, Any]:
    """Return a JSON object or raise a contract-level validation error."""

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise RequestValidationError("JSON istek gövdesi bir nesne olmalıdır.")
    return payload


def _required_text(
    payload: Dict[str, Any],
    field_name: str,
    label: str,
    max_length: int,
) -> str:
    """Normalize and validate one required text field."""

    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError(f"{label} alanı zorunludur.")

    normalized = value.strip()
    if len(normalized) > max_length:
        raise RequestValidationError(
            f"{label} alanı en fazla {max_length} karakter olabilir."
        )
    return normalized


def _optional_text(
    payload: Dict[str, Any],
    field_name: str,
    label: str,
    max_length: int,
) -> Optional[str]:
    """Normalize and validate one optional text field."""

    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RequestValidationError(f"{label} alanı metin olmalıdır.")

    normalized = value.strip()
    if len(normalized) > max_length:
        raise RequestValidationError(
            f"{label} alanı en fazla {max_length} karakter olabilir."
        )
    return normalized or None


def _validated_history(value: Any) -> List[Dict[str, str]]:
    """Validate the public shape of optional conversation history."""

    if value is None:
        return []
    if not isinstance(value, list):
        raise RequestValidationError("gecmis alanı bir liste olmalıdır.")

    history: List[Dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise RequestValidationError(
                f"gecmis[{index}] bir nesne olmalıdır."
            )

        role = item.get("role")
        content = item.get("content")
        if role not in ALLOWED_HISTORY_ROLES:
            raise RequestValidationError(
                "Sohbet geçmişinde yalnızca user ve assistant rolleri kullanılabilir."
            )
        if not isinstance(content, str) or not content.strip():
            raise RequestValidationError(
                f"gecmis[{index}].content boş olmayan bir metin olmalıdır."
            )

        normalized_content = content.strip()
        if len(normalized_content) > HISTORY_MESSAGE_MAX_LENGTH:
            raise RequestValidationError(
                f"Geçmiş mesajlar en fazla {HISTORY_MESSAGE_MAX_LENGTH} karakter olabilir."
            )
        history.append({"role": role, "content": normalized_content})

    return history


@main.get("/")
def index() -> str:
    """Render the backend fallback landing page."""

    return render_template("index.html")


@main.get("/dashboard")
@admin_page_required
def dashboard() -> str:
    """Render the backend fallback dashboard page."""

    return render_template("dashboard.html", csrf_token=get_csrf_token())


@main.post("/api/sohbet")
def sohbet() -> Tuple[Response, int]:
    """Validate a visitor message and delegate response generation to AIService."""

    retry_after = _chat_retry_after()
    if retry_after:
        response, status_code = _error_response(
            "RATE_LIMITED",
            "Çok fazla sohbet isteği gönderildi. Lütfen kısa süre sonra tekrar deneyin.",
            429,
        )
        response.headers["Retry-After"] = str(retry_after)
        return response, status_code

    try:
        payload = _json_object()
        message = _required_text(
            payload,
            "mesaj",
            "mesaj",
            CHAT_MESSAGE_MAX_LENGTH,
        )
        history = _validated_history(payload.get("gecmis"))
        answer = ai_service.yanit_uret(message, history)
    except RequestValidationError as exc:
        return _error_response("VALIDATION_ERROR", str(exc), 400)
    except ValueError:
        current_app.logger.warning("AI servisine geçersiz doğrulanmış veri iletildi.")
        return _error_response(
            "VALIDATION_ERROR",
            "Sohbet isteği geçersiz.",
            400,
        )
    except AIServiceError:
        current_app.logger.exception("AI servis isteği başarısız oldu.")
        return _error_response(
            "AI_SERVICE_UNAVAILABLE",
            "AI servisine şu anda ulaşılamıyor. Lütfen tekrar deneyin.",
            503,
        )

    return jsonify({"basari": True, "cevap": answer}), 200


@main.post("/api/leads")
def lead_olustur() -> Tuple[Response, int]:
    """Validate and persist one visitor lead."""

    try:
        payload = _json_object()
        if "id" in payload or "tarih" in payload:
            raise RequestValidationError(
                "id ve tarih alanları sunucu tarafından oluşturulur."
            )

        name = _required_text(payload, "isim", "isim", NAME_MAX_LENGTH)
        phone = _required_text(payload, "telefon", "telefon", PHONE_MAX_LENGTH)
        message = _optional_text(
            payload,
            "mesaj",
            "mesaj",
            LEAD_MESSAGE_MAX_LENGTH,
        )
        lead_id = lead_ekle(name, phone, message)
    except RequestValidationError as exc:
        return _error_response("VALIDATION_ERROR", str(exc), 400)
    except sqlite3.Error:
        current_app.logger.exception("Lead kaydı veritabanına yazılamadı.")
        return _error_response(
            "DATABASE_ERROR",
            "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
            500,
        )

    current_app.logger.info("Lead kaydı oluşturuldu. lead_id=%s", lead_id)
    return (
        jsonify(
            {
                "basari": True,
                "mesaj": "İletişim bilgileriniz kaydedildi.",
            }
        ),
        201,
    )


@main.get("/api/leads")
@admin_api_required
def leadleri_listele() -> Tuple[Response, int]:
    """Return all leads newest-first."""

    try:
        leads = tum_leadler()
    except sqlite3.Error:
        current_app.logger.exception("Lead listesi veritabanından okunamadı.")
        return _error_response(
            "DATABASE_ERROR",
            "İşlem tamamlanamadı. Lütfen tekrar deneyin.",
            500,
        )
    return jsonify({"basari": True, "leads": leads}), 200
