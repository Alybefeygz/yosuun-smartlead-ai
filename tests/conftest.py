"""Shared pytest fixtures."""

import pytest
from werkzeug.security import generate_password_hash

from app import create_app


TEST_ADMIN_USERNAME = "test-admin"
TEST_ADMIN_PASSWORD = "correct-horse-battery-staple"
TEST_ADMIN_PASSWORD_HASH = generate_password_hash(
    TEST_ADMIN_PASSWORD,
    method="pbkdf2:sha256:1000",
)


@pytest.fixture
def app(tmp_path):
    """Create an isolated Flask app backed by a temporary SQLite file."""

    application = create_app(
        "development",
        {
            "TESTING": True,
            "DATABASE_URL": str(tmp_path / "test.sqlite3"),
            "ADMIN_USERNAME": TEST_ADMIN_USERNAME,
            "ADMIN_PASSWORD_HASH": TEST_ADMIN_PASSWORD_HASH,
            "AUTH_MAX_ATTEMPTS": 3,
            "AUTH_ATTEMPT_WINDOW_SECONDS": 60,
            "AUTH_LOCKOUT_SECONDS": 120,
        },
    )
    return application


@pytest.fixture
def client(app):
    """Return a Flask test client for the isolated application."""

    return app.test_client()


@pytest.fixture
def admin_headers(client):
    """Return an Authorization header carrying a valid admin bearer token."""

    response = client.post(
        "/api/admin/token",
        json={
            "kullanici_adi": TEST_ADMIN_USERNAME,
            "parola": TEST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['token']}"}
