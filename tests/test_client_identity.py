"""Tests for per-visitor rate limiting of requests forwarded by the Wix site."""

import pytest

import app.routes as routes_module
from app.auth import LoginAttemptLimiter
from app.client_identity import (
    WIX_ANONYMOUS_KEY,
    ClientIdentity,
    resolve_client_identity,
)
from app.services.rate_limiter import SlidingWindowRateLimiter
from tests.conftest import TEST_ADMIN_PASSWORD, TEST_ADMIN_USERNAME


WIX_SECRET = "test-wix-shared-secret"
VISITOR_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
VISITOR_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


@pytest.fixture
def wix_app(app):
    app.config.update(
        WIX_SHARED_SECRET=WIX_SECRET,
        CHAT_RATE_LIMIT_REQUESTS=2,
        WIX_CHAT_RATE_LIMIT_REQUESTS=3,
    )
    routes_module.init_chat_rate_limit(app)
    return app


@pytest.fixture
def wix_client(wix_app, monkeypatch):
    monkeypatch.setattr(
        routes_module.ai_service,
        "yanit_uret",
        lambda *_args, **_kwargs: "cevap",
    )
    return wix_app.test_client()


def wix_headers(client_id=None, secret=WIX_SECRET):
    headers = {"X-Wix-Secret": secret}
    if client_id is not None:
        headers["X-Client-Id"] = client_id
    return headers


def identity_for(app, headers):
    with app.test_request_context(
        "/api/sohbet",
        headers=headers,
        environ_base={"REMOTE_ADDR": "203.0.113.7"},
    ):
        return resolve_client_identity()


def chat(client, headers):
    return client.post("/api/sohbet", json={"mesaj": "Merhaba"}, headers=headers)


def test_valid_secret_and_visitor_id_identify_the_visitor(wix_app):
    assert identity_for(wix_app, wix_headers(VISITOR_A)) == ClientIdentity(
        key=f"wix:{VISITOR_A}",
        via_wix=True,
    )


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Client-Id": VISITOR_A},
        wix_headers(VISITOR_A, secret="wrong-secret"),
    ],
)
def test_requests_without_valid_secret_fall_back_to_ip(wix_app, headers):
    assert identity_for(wix_app, headers) == ClientIdentity(
        key="ip:203.0.113.7",
        via_wix=False,
    )


def test_visitor_ids_are_ignored_when_no_secret_is_configured(app):
    app.config["WIX_SHARED_SECRET"] = None

    assert identity_for(app, wix_headers(VISITOR_A)).key == "ip:203.0.113.7"


@pytest.mark.parametrize(
    "client_id",
    [None, "", "short", "x" * 65, "has space in the identifier", "semi;colon-0123456789"],
)
def test_wix_requests_with_unusable_visitor_id_share_one_bucket(wix_app, client_id):
    assert identity_for(wix_app, wix_headers(client_id)) == ClientIdentity(
        key=WIX_ANONYMOUS_KEY,
        via_wix=True,
    )


def test_wix_visitors_have_separate_chat_limits(wix_client):
    for _index in range(2):
        assert chat(wix_client, wix_headers(VISITOR_A)).status_code == 200

    assert chat(wix_client, wix_headers(VISITOR_A)).status_code == 429
    assert chat(wix_client, wix_headers(VISITOR_B)).status_code == 200


def test_wix_wide_limit_caps_rotating_visitor_ids(wix_client):
    for index in range(3):
        visitor = f"rotating-visitor-{index:04d}"
        assert chat(wix_client, wix_headers(visitor)).status_code == 200

    blocked = chat(wix_client, wix_headers("rotating-visitor-9999"))

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_direct_requests_do_not_use_the_wix_wide_limit(wix_client):
    for index in range(3):
        chat(wix_client, wix_headers(f"rotating-visitor-{index:04d}"))

    assert chat(wix_client, {}).status_code == 200


def test_admin_lockout_applies_only_to_the_failing_visitor(wix_client):
    def request_token(client_id, password):
        return wix_client.post(
            "/api/admin/token",
            json={"kullanici_adi": TEST_ADMIN_USERNAME, "parola": password},
            headers=wix_headers(client_id),
        )

    for _index in range(3):
        assert request_token(VISITOR_A, "wrong").status_code == 401

    assert request_token(VISITOR_A, TEST_ADMIN_PASSWORD).status_code == 429
    assert request_token(VISITOR_B, TEST_ADMIN_PASSWORD).status_code == 200


def test_rate_limiter_forgets_idle_clients(monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "app.services.rate_limiter.monotonic",
        lambda: clock["now"],
    )
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=10)

    limiter.acquire("idle-visitor")
    clock["now"] += 11
    limiter.acquire("active-visitor")

    assert list(limiter._requests) == ["active-visitor"]


def test_login_limiter_forgets_expired_lockouts_and_idle_clients(monkeypatch):
    clock = {"now": 100.0}
    monkeypatch.setattr("app.auth.monotonic", lambda: clock["now"])
    limiter = LoginAttemptLimiter(max_attempts=1, window_seconds=10, lockout_seconds=20)

    limiter.register_failure("old-visitor")
    clock["now"] += 21
    limiter.register_failure("new-visitor")

    assert "old-visitor" not in limiter._blocked_until
    assert "old-visitor" not in limiter._attempts
