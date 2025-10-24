from __future__ import annotations

import os
import pytest
from tests.utils.events import make_event, parse_body


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────


def _call(event):
    """Invoke the auth Lambda handler directly."""
    from src.handlers import auth as handler

    return handler.lambda_handler(event, None)


def _creds() -> tuple[str, str]:
    """Return configured or default test credentials."""
    return (
        os.getenv("PYTEST_USERNAME", "bob"),
        os.getenv("PYTEST_PASSWORD", "secret123"),
    )


def _login(username: str, password: str):
    """Helper to call /auth/login and parse its body."""
    event = make_event(
        "POST", "/auth/login", body={"username": username, "password": password}
    )
    resp = _call(event)
    return resp, parse_body(resp)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def auth_login_result():
    """Attempt login once per session for reuse across tests."""
    username, password = _creds()
    resp, body = _login(username, password)
    return {"status": resp.get("statusCode"), "body": body, "username": username}


# ──────────────────────────────────────────────────────────────────────────────
# Unit / Integration tests
# ──────────────────────────────────────────────────────────────────────────────


def test_login_preflight(auth_login_result):
    """Login should yield 200 OK or 202 challenge."""
    assert auth_login_result["status"] in (
        200,
        202,
    ), f"Unexpected login result: {auth_login_result}"


def test_login_ok(auth_login_result):
    """When login succeeds, it must return tokens as per OpenAPI spec."""
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge path handled separately.")
    body = auth_login_result["body"]
    assert set(body) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_login_challenge(auth_login_result):
    """When challenge required, schema must match NEW_PASSWORD_REQUIRED spec."""
    if auth_login_result["status"] == 200:
        pytest.skip("Challenge not triggered.")
    body = auth_login_result["body"]
    assert auth_login_result["status"] == 202
    assert body["challenge"] == "NEW_PASSWORD_REQUIRED"
    assert set(body) == {"username", "challenge", "session"}


def test_login_invalid_credentials():
    """Invalid password should yield 401 Unauthorized."""
    username, _ = _creds()
    event = make_event(
        "POST", "/auth/login", body={"username": username, "password": "wrongpassword"}
    )
    resp = _call(event)
    assert resp["statusCode"] == 401


def test_refresh_ok(auth_login_result):
    """Refresh with valid token must succeed and return full token set."""
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge flow incomplete.")
    username, _ = _creds()
    refresh_token = auth_login_result["body"]["refreshToken"]
    event = make_event(
        "POST",
        "/auth/refresh",
        body={"username": username, "refreshToken": refresh_token},
    )
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert set(body) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_logout_ok(auth_login_result):
    """Logout with valid token should return 204 No Content."""
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge flow incomplete.")
    username, _ = _creds()
    refresh_token = auth_login_result["body"]["refreshToken"]
    event = make_event(
        "POST",
        "/auth/logout",
        body={"username": username, "refreshToken": refresh_token},
    )
    resp = _call(event)
    assert resp["statusCode"] == 204


# ──────────────────────────────────────────────────────────────────────────────
# End-to-End Authentication flow (follows OpenAPI spec)
# ──────────────────────────────────────────────────────────────────────────────


def test_auth_e2e():
    username, password = _creds()

    # 1. Login (handle challenge if needed)
    resp, body = _login(username, password)
    status = resp.get("statusCode")

    if status == 202:
        assert body.get("challenge") == "NEW_PASSWORD_REQUIRED"
        session = body.get("session")
        assert session, "Missing session in challenge response"

        reset_event = make_event(
            "POST",
            "/auth/reset",
            body={"username": username, "session": session, "newPassword": password},
        )
        reset_resp = _call(reset_event)
        assert reset_resp["statusCode"] == 204, reset_resp

        resp, body = _login(username, password)
        status = resp.get("statusCode")

    assert status == 200, f"Expected 200 after challenge; got {status}"
    assert set(body) == {"user", "accessToken", "refreshToken", "expiresIn"}

    # 2. Refresh
    refresh_event = make_event(
        "POST",
        "/auth/refresh",
        body={"username": username, "refreshToken": body["refreshToken"]},
    )
    refresh_resp = _call(refresh_event)
    assert refresh_resp["statusCode"] == 200
    refresh_body = parse_body(refresh_resp)
    assert set(refresh_body) == {"user", "accessToken", "refreshToken", "expiresIn"}

    # 3. Logout (new signature expects username + refreshToken in body)
    logout_event = make_event(
        "POST",
        "/auth/logout",
        body={"username": username, "refreshToken": refresh_body["refreshToken"]},
    )
    logout_resp = _call(logout_event)
    assert logout_resp["statusCode"] == 204

    # 4. Forget
    forget_event = make_event("POST", "/auth/forget", body={"username": username})
    forget_resp = _call(forget_event)
    assert forget_resp["statusCode"] == 204
