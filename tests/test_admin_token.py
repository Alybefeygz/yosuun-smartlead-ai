"""Integration tests for the bearer-token admin API used by the Wix site."""

from datetime import timedelta

from werkzeug.security import generate_password_hash

from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME


def request_token(client, username=TEST_ADMIN_USERNAME, password=TEST_ADMIN_PASSWORD):
    return client.post(
        "/api/admin/token",
        json={"kullanici_adi": username, "parola": password},
    )


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_valid_credentials_return_token(client):
    response = request_token(client)
    body = response.get_json()

    assert response.status_code == 200
    assert body["basari"] is True
    assert isinstance(body["token"], str) and body["token"]
    assert body["sure_saniye"] == 30 * 60


def test_token_unlocks_lead_listing_without_session(client):
    client.post("/api/leads", json={"isim": "Wix Test", "telefon": "05550000000"})
    token = request_token(client).get_json()["token"]

    response = client.get("/api/leads", headers=bearer(token))

    assert response.status_code == 200
    assert response.get_json()["leads"][0]["isim"] == "Wix Test"
    assert client.get("/dashboard").status_code == 302


def test_invalid_credentials_use_generic_error_and_never_echo_password(client):
    attempted_password = "wrong-private-password"
    response = request_token(client, password=attempted_password)

    assert response.status_code == 401
    assert response.get_json() == {
        "basari": False,
        "hata": {
            "kod": "AUTH_FAILED",
            "mesaj": "Kullanıcı adı veya parola hatalı.",
        },
    }
    assert attempted_password not in response.get_data(as_text=True)


def test_non_object_body_is_rejected(client):
    response = client.post("/api/admin/token", data="kullanici_adi=x")

    assert response.status_code == 400
    assert response.get_json()["hata"]["kod"] == "VALIDATION_ERROR"


def test_non_string_credentials_are_treated_as_invalid(client):
    response = client.post(
        "/api/admin/token",
        json={"kullanici_adi": ["admin"], "parola": 123},
    )

    assert response.status_code == 401


def test_forged_or_malformed_tokens_are_rejected(client):
    for header in (
        bearer("not-a-real-token"),
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer "},
    ):
        assert client.get("/api/leads", headers=header).status_code == 401


def test_token_signed_with_other_secret_is_rejected(app, client):
    token = request_token(client).get_json()["token"]
    app.secret_key = "rotated-secret-key"

    assert client.get("/api/leads", headers=bearer(token)).status_code == 401


def test_expired_token_is_rejected(app, client):
    token = request_token(client).get_json()["token"]
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=-1)

    assert client.get("/api/leads", headers=bearer(token)).status_code == 401


def test_password_hash_rotation_invalidates_existing_token(app, client):
    token = request_token(client).get_json()["token"]
    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(
        "rotated-password",
        method="pbkdf2:sha256:1000",
    )

    assert client.get("/api/leads", headers=bearer(token)).status_code == 401


def test_token_failures_share_login_rate_limit(client):
    for _index in range(3):
        assert request_token(client, password="wrong").status_code == 401

    blocked = request_token(client)

    assert blocked.status_code == 429
    assert blocked.get_json()["hata"]["kod"] == "RATE_LIMITED"
    assert int(blocked.headers["Retry-After"]) > 0


def test_missing_admin_configuration_returns_503(app, client):
    app.config["ADMIN_PASSWORD_HASH"] = None

    response = request_token(client)

    assert response.status_code == 503
    assert response.get_json()["hata"]["kod"] == "AUTH_UNAVAILABLE"


def test_token_responses_disable_caching(client):
    response = request_token(client)

    assert response.headers["Cache-Control"] == "no-store"
