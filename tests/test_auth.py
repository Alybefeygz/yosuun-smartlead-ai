"""Integration tests for administrator authentication and authorization."""

from werkzeug.security import generate_password_hash

from app import create_app
from config import ProductionConfig
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME


def csrf_token(client) -> str:
    client.get("/login")
    with client.session_transaction() as active_session:
        return active_session["csrf_token"]


def login(client, password=TEST_ADMIN_PASSWORD, username=TEST_ADMIN_USERNAME):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_token(client),
        },
    )


def test_anonymous_dashboard_redirects_to_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


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


def test_valid_login_unlocks_dashboard_and_lead_api(client):
    response = login(client)

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/dashboard")
    assert client.get("/dashboard").status_code == 200
    assert client.get("/api/leads").status_code == 200


def test_invalid_login_uses_generic_error_and_never_echoes_password(client):
    attempted_password = "wrong-private-password"
    response = login(client, password=attempted_password)
    body = response.get_data(as_text=True)

    assert response.status_code == 401
    assert "Kullanıcı adı veya parola hatalı." in body
    assert attempted_password not in body
    assert client.get("/dashboard").status_code == 302


def test_login_requires_valid_csrf_token(client):
    response = client.post(
        "/login",
        data={
            "username": TEST_ADMIN_USERNAME,
            "password": TEST_ADMIN_PASSWORD,
            "csrf_token": "invalid",
        },
    )

    assert response.status_code == 400
    assert client.get("/dashboard").status_code == 302


def test_repeated_failures_are_rate_limited(client):
    for _index in range(3):
        assert login(client, password="wrong").status_code == 401

    blocked = login(client, password="wrong")

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_logout_requires_csrf_and_ends_session(authenticated_client):
    invalid = authenticated_client.post("/logout", data={"csrf_token": "invalid"})
    assert invalid.status_code == 400
    assert authenticated_client.get("/dashboard").status_code == 200

    with authenticated_client.session_transaction() as active_session:
        token = active_session["csrf_token"]
    response = authenticated_client.post("/logout", data={"csrf_token": token})

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/login")
    assert authenticated_client.get("/dashboard").status_code == 302


def test_password_hash_rotation_invalidates_existing_session(
    app,
    authenticated_client,
):
    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(
        "rotated-password",
        method="pbkdf2:sha256:1000",
    )

    assert authenticated_client.get("/dashboard").status_code == 302
    assert authenticated_client.get("/api/leads").status_code == 401


def test_sensitive_routes_disable_browser_caching(authenticated_client):
    for path in ("/login", "/dashboard", "/api/leads"):
        response = authenticated_client.get(path)
        assert response.headers["Cache-Control"] == "no-store"


def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_production_session_cookie_and_hsts_are_enforced(tmp_path, monkeypatch):
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

    response = app.test_client().get("/login")
    cookie = response.headers["Set-Cookie"]

    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
