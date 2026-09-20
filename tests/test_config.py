"""Tests for environment selection and safe configuration defaults."""

import pytest

from app import create_app
from config import (
    ProductionConfig,
    _parse_positive_int,
    _parse_temperature,
    resolve_config,
)


def test_development_app_uses_expected_safe_defaults(tmp_path):
    app = create_app(
        "development",
        {"DATABASE_URL": str(tmp_path / "config-test.sqlite3")},
    )

    assert app.config["DEBUG"] is True
    assert app.config["AI_PROVIDER"] == "groq"
    assert app.config["GROQ_MODEL"] == "openai/gpt-oss-20b"
    assert app.config["AI_HISTORY_MAX_MESSAGES"] == 20
    assert app.config["AI_HISTORY_MAX_CHARS"] == 8000
    assert app.config["AI_TEMPERATURE"] == 0.3
    assert app.config["AI_MAX_COMPLETION_TOKENS"] == 500
    assert app.config["AI_KNOWLEDGE_MAX_SECTIONS"] == 4
    assert app.config["AI_KNOWLEDGE_MAX_CHARS"] == 7000
    assert app.config["KNOWLEDGE_BASE_PATH"].endswith("knowledge/yosuun.md")
    assert app.config["CHAT_RATE_LIMIT_REQUESTS"] == 10
    assert app.config["MAX_CONTENT_LENGTH"] == 65536


@pytest.mark.parametrize("raw_value", ["", "0", "-1", "invalid"])
def test_invalid_timeout_uses_safe_default(raw_value):
    assert _parse_positive_int(raw_value, default=20) == 20


@pytest.mark.parametrize("raw_value", ["", "-0.1", "2.1", "invalid"])
def test_invalid_temperature_uses_safe_default(raw_value):
    assert _parse_temperature(raw_value, default=0.3) == 0.3


@pytest.mark.parametrize("raw_value", ["0", "0.3", "2"])
def test_valid_temperature_is_parsed(raw_value):
    assert _parse_temperature(raw_value, default=1.0) == float(raw_value)


def test_unknown_environment_is_rejected():
    with pytest.raises(ValueError, match="Bilinmeyen ortam"):
        resolve_config("staging")


def test_production_requires_secret_key(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        ProductionConfig.validate()


def test_production_requires_admin_username(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "production-secret")
    monkeypatch.setattr(ProductionConfig, "ADMIN_USERNAME", None)
    monkeypatch.setattr(ProductionConfig, "ADMIN_PASSWORD_HASH", "valid-hash")

    with pytest.raises(RuntimeError, match="ADMIN_USERNAME"):
        ProductionConfig.validate()


def test_production_requires_admin_password_hash(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "production-secret")
    monkeypatch.setattr(ProductionConfig, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(ProductionConfig, "ADMIN_PASSWORD_HASH", None)

    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD_HASH"):
        ProductionConfig.validate()


def test_production_uses_secure_session_cookie():
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
    assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"
