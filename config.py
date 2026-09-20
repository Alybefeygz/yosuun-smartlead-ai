"""Environment-backed configuration for the Yosuun SmartLead application."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Optional, Type

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = BASE_DIR / "instance" / "yosuun.sqlite3"
DEFAULT_KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge" / "yosuun.md"

# Loading a local .env here keeps every environment lookup in one boundary.
# Production values are supplied directly by Render environment variables.
load_dotenv(BASE_DIR / ".env")


def _parse_positive_int(raw_value: str, default: int) -> int:
    """Return a positive integer while keeping invalid local config safe."""

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _parse_temperature(raw_value: str, default: float) -> float:
    """Return a Groq-compatible temperature or a deterministic safe default."""

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return default
    return value if 0 <= value <= 2 else default


class Config:
    """Settings shared by all runtime environments."""

    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY") or None
    ADMIN_USERNAME: Optional[str] = os.getenv("ADMIN_USERNAME") or None
    ADMIN_PASSWORD_HASH: Optional[str] = os.getenv("ADMIN_PASSWORD_HASH") or None
    DATABASE_URL = os.getenv("DATABASE_URL", str(DEFAULT_DATABASE_PATH))
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY") or None
    AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").strip().lower()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    AI_TIMEOUT_SECONDS = _parse_positive_int(
        os.getenv("AI_TIMEOUT_SECONDS", "20"),
        default=20,
    )
    AI_HISTORY_MAX_MESSAGES = _parse_positive_int(
        os.getenv("AI_HISTORY_MAX_MESSAGES", "20"),
        default=20,
    )
    AI_HISTORY_MAX_CHARS = _parse_positive_int(
        os.getenv("AI_HISTORY_MAX_CHARS", "8000"),
        default=8000,
    )
    AI_TEMPERATURE = _parse_temperature(
        os.getenv("AI_TEMPERATURE", "0.3"),
        default=0.3,
    )
    AI_MAX_COMPLETION_TOKENS = _parse_positive_int(
        os.getenv("AI_MAX_COMPLETION_TOKENS", "500"),
        default=500,
    )
    AI_KNOWLEDGE_MAX_SECTIONS = _parse_positive_int(
        os.getenv("AI_KNOWLEDGE_MAX_SECTIONS", "4"),
        default=4,
    )
    AI_KNOWLEDGE_MAX_CHARS = _parse_positive_int(
        os.getenv("AI_KNOWLEDGE_MAX_CHARS", "7000"),
        default=7000,
    )
    KNOWLEDGE_BASE_PATH = os.getenv(
        "KNOWLEDGE_BASE_PATH",
        str(DEFAULT_KNOWLEDGE_BASE_PATH),
    ).strip()
    CHAT_RATE_LIMIT_REQUESTS = _parse_positive_int(
        os.getenv("CHAT_RATE_LIMIT_REQUESTS", "10"),
        default=10,
    )
    CHAT_RATE_LIMIT_WINDOW_SECONDS = _parse_positive_int(
        os.getenv("CHAT_RATE_LIMIT_WINDOW_SECONDS", "60"),
        default=60,
    )
    MAX_CONTENT_LENGTH = _parse_positive_int(
        os.getenv("MAX_CONTENT_LENGTH", "65536"),
        default=65536,
    )
    AUTH_MAX_ATTEMPTS = _parse_positive_int(
        os.getenv("AUTH_MAX_ATTEMPTS", "5"),
        default=5,
    )
    AUTH_ATTEMPT_WINDOW_SECONDS = _parse_positive_int(
        os.getenv("AUTH_ATTEMPT_WINDOW_SECONDS", "300"),
        default=300,
    )
    AUTH_LOCKOUT_SECONDS = _parse_positive_int(
        os.getenv("AUTH_LOCKOUT_SECONDS", "600"),
        default=600,
    )
    BUSINESS_CONTEXT = os.getenv(
        "BUSINESS_CONTEXT",
        """Sen Yosuun E-Ticaret Ekosistemi'nin yapay zekâ asistanısın.
Yosuun; e-ticaret markaları, satıcıları ve operasyon ekiplerinin ürün, stok,
rakip ve operasyon süreçlerini tek merkezden yönetmesine yardımcı olan yapay
zekâ destekli bir SaaS platformudur.

Ana marka yaklaşımı: “Sen hayatını yaşa, e-ticareti Yosuun halletsin.”
“Kontrol hâlâ bende. Yük artık değil.”""",
    ).strip()

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    TRUST_PROXY_HEADERS = False

    @classmethod
    def validate(cls) -> None:
        """Validate values that every environment must provide."""

        if not cls.DATABASE_URL:
            raise RuntimeError("DATABASE_URL boş olamaz.")
        if not cls.BUSINESS_CONTEXT:
            raise RuntimeError("BUSINESS_CONTEXT boş olamaz.")
        if not cls.GROQ_MODEL:
            raise RuntimeError("GROQ_MODEL boş olamaz.")
        if not cls.KNOWLEDGE_BASE_PATH:
            raise RuntimeError("KNOWLEDGE_BASE_PATH boş olamaz.")


class DevelopmentConfig(Config):
    """Safe defaults intended only for local development."""

    DEBUG = True
    SECRET_KEY = Config.SECRET_KEY or "development-only-change-me"


class ProductionConfig(Config):
    """Production settings with strict secret validation."""

    SESSION_COOKIE_SECURE = True
    TRUST_PROXY_HEADERS = True

    @classmethod
    def validate(cls) -> None:
        super().validate()
        if not cls.SECRET_KEY:
            raise RuntimeError("Production ortamında SECRET_KEY zorunludur.")
        if not cls.ADMIN_USERNAME:
            raise RuntimeError("Production ortamında ADMIN_USERNAME zorunludur.")
        if not cls.ADMIN_PASSWORD_HASH:
            raise RuntimeError("Production ortamında ADMIN_PASSWORD_HASH zorunludur.")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def resolve_config(config_name: Optional[str] = None) -> Type[Config]:
    """Resolve and validate a configuration class by environment name."""

    selected_name = (config_name or os.getenv("FLASK_ENV", "development")).lower()
    try:
        config_class = config_by_name[selected_name]
    except KeyError as exc:
        valid_names = ", ".join(sorted(config_by_name))
        raise ValueError(
            f"Bilinmeyen ortam: {selected_name}. Geçerli değerler: {valid_names}."
        ) from exc

    config_class.validate()
    return config_class
