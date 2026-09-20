"""Environment-backed configuration for the Yosuun SmartLead application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Type

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = BASE_DIR / "instance" / "yosuun.sqlite3"

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


class Config:
    """Settings shared by all runtime environments."""

    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY") or None
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
    MAX_CONTENT_LENGTH = _parse_positive_int(
        os.getenv("MAX_CONTENT_LENGTH", "65536"),
        default=65536,
    )
    BUSINESS_CONTEXT = os.getenv(
        "BUSINESS_CONTEXT",
        """Sen Yosuun E-Ticaret Ekosistemi'nin yapay zekâ asistanısın.
Yosuun; e-ticaret markaları, satıcıları ve operasyon ekiplerinin ürün, stok,
rakip ve operasyon süreçlerini tek merkezden yönetmesine yardımcı olan yapay
zekâ destekli bir SaaS platformudur.

Yosuun hakkında açık, kısa ve doğru bilgi ver. Kullanıcı ihtiyacını anlamaya
yardımcı ol; bilmediğin özellikleri varmış gibi söyleme. Uygun kullanıcıyı
iletişim bilgisi bırakmaya yönlendir. Türkçe, sade, profesyonel ve samimi
konuş. Şifre, kart bilgisi veya API anahtarı gibi hassas bilgi isteme.
Ana marka yaklaşımı: Sen hayatını yaşa, e-ticareti Yosuun halletsin.""",
    ).strip()

    DEBUG = False
    TESTING = False

    @classmethod
    def validate(cls) -> None:
        """Validate values that every environment must provide."""

        if not cls.DATABASE_URL:
            raise RuntimeError("DATABASE_URL boş olamaz.")
        if not cls.BUSINESS_CONTEXT:
            raise RuntimeError("BUSINESS_CONTEXT boş olamaz.")
        if not cls.GROQ_MODEL:
            raise RuntimeError("GROQ_MODEL boş olamaz.")


class DevelopmentConfig(Config):
    """Safe defaults intended only for local development."""

    DEBUG = True
    SECRET_KEY = Config.SECRET_KEY or "development-only-change-me"


class ProductionConfig(Config):
    """Production settings with strict secret validation."""

    @classmethod
    def validate(cls) -> None:
        super().validate()
        if not cls.SECRET_KEY:
            raise RuntimeError("Production ortamında SECRET_KEY zorunludur.")


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
