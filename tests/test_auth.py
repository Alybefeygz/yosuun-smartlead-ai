"""Integration tests for API authorization boundaries and security headers."""

from werkzeug.security import generate_password_hash

from app import create_app
from config import ProductionConfig
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME


def test_anonymous_lead_listing_returns_json_401(client):
    response = client.get("/api/leads")

    assert response.status_code == 401
    assert response.get_json() == {
        "basari": False,
        "hata": {
            "kod": "AUTH_REQUIRED",
            "mesaj": "Bu işlem için yönetici girişi gereklidir.",
        },
    }


def test_public_lead_creation_remains_available(client):
    response = client.post(
        "/api/leads",
        json={"isim": "Test Kullanıcı", "telefon": "05550000000"},
    )

    assert response.status_code == 201


def test_removed_html_pages_are_not_served(client):
    for path in ("/", "/login", "/dashboard"):
        assert client.get(path).status_code == 404


def test_lead_listing_disables_caching(client, admin_headers):
    response = client.get("/api/leads", headers=admin_headers)

    assert response.headers["Cache-Control"] == "no-store"


def test_security_headers_are_present(client):
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_production_enforces_hsts(tmp_path, monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "production-test-secret")
    monkeypatch.setattr(ProductionConfig, "ADMIN_USERNAME", TEST_ADMIN_USERNAME)
    monkeypatch.setattr(
        ProductionConfig,
        "ADMIN_PASSWORD_HASH",
        generate_password_hash(
            TEST_ADMIN_PASSWORD,
            method="pbkdf2:sha256:1000",
        ),
    )
    app = create_app(
        "production",
        {
            "TESTING": True,
            "DATABASE_URL": str(tmp_path / "production.sqlite3"),
            "TRUST_PROXY_HEADERS": False,
        },
    )

    response = app.test_client().get("/health")

    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
