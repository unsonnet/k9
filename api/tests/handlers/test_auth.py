from __future__ import annotations

import os
import pytest
from tests.utils.events import make_event, parse_body
from tests.utils.handlers import call_handler


def _creds():
    username = os.getenv("PYTEST_USER_USERNAME")
    password = os.getenv("PYTEST_USER_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Environment variables PYTEST_USER_USERNAME and PYTEST_USER_PASSWORD "
            "must be set to run authentication tests."
        )
    return username, password


def _login(username: str, password: str):
    event = make_event(
        "POST", "/auth/login", body={"username": username, "password": password}
    )
    resp = call_handler("auth", event)
    return resp, parse_body(resp)


@pytest.fixture(scope="session")
def auth_login_result():
    username, password = _creds()
    resp, body = _login(username, password)
    return {"status": resp.get("statusCode"), "body": body, "username": username}


def test_login_preflight(auth_login_result):
    assert auth_login_result["status"] in (200, 202)


def test_login_ok(auth_login_result):
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge case tested separately")
    body = auth_login_result["body"]
    assert set(body) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_login_challenge(auth_login_result):
    if auth_login_result["status"] == 200:
        pytest.skip("No challenge triggered")
    body = auth_login_result["body"]
    assert auth_login_result["status"] == 202
    assert body["challenge"] == "NEW_PASSWORD_REQUIRED"
    assert set(body) == {"username", "challenge", "session"}


def test_login_invalid_credentials():
    username, _ = _creds()
    event = make_event(
        "POST", "/auth/login", body={"username": username, "password": "wrongpassword"}
    )
    resp = call_handler("auth", event)
    assert resp["statusCode"] == 401


def test_refresh_ok(auth_login_result):
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge case incomplete")
    refresh_token = auth_login_result["body"]["refreshToken"]
    username, _ = _creds()
    event = make_event(
        "POST",
        "/auth/refresh",
        body={"username": username, "refreshToken": refresh_token},
    )
    resp = call_handler("auth", event)
    assert resp["statusCode"] == 200
    assert set(parse_body(resp)) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_logout_ok(auth_login_result):
    if auth_login_result["status"] == 202:
        pytest.skip("Challenge case incomplete")
    refresh_token = auth_login_result["body"]["refreshToken"]
    username, _ = _creds()
    event = make_event(
        "POST",
        "/auth/logout",
        body={"username": username, "refreshToken": refresh_token},
    )
    resp = call_handler("auth", event)
    assert resp["statusCode"] == 204
