from __future__ import annotations

import os
import uuid
from typing import Generator, Any
import pytest
from tests.utils.events import make_event, parse_body


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────


def _call_user(event):
    from src.handlers import user as handler

    return handler.lambda_handler(event, None)


def _call_auth(event):
    from src.handlers import auth as handler

    return handler.lambda_handler(event, None)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _force_success_login(username: str, password: str) -> dict[str, Any]:
    """
    For accounts that are already initialized with no challenge.
    Mandatory for admin/user fixtures.
    """
    login_event = make_event(
        "POST", "/auth/login", body={"username": username, "password": password}
    )
    login_resp = _call_auth(login_event)
    status = login_resp.get("statusCode")
    if status != 200:
        raise RuntimeError(
            f"Login for [{username}] MUST be 200 OK, got {status}. "
            "Fix your environment users: admin + default test user must be pre-initialized"
        )
    body = parse_body(login_resp)
    assert set(body) == {"user", "accessToken", "refreshToken", "expiresIn"}
    return body


def _force_user_established(username: str, temp_password: str) -> dict[str, str]:
    """
    Required flow for newly created users:

    1. POST /auth/login → 202 NEW_PASSWORD_REQUIRED
    2. POST /auth/reset → 204
    3. POST /auth/login → 200 WITH access + refresh + user UUID

    Returns:
        { "user": UUID, "token": accessToken }
    """
    # First login must trigger 202 challenge
    first_login_event = make_event(
        "POST",
        "/auth/login",
        body={"username": username, "password": temp_password},
    )
    first_login = _call_auth(first_login_event)
    status = first_login.get("statusCode")
    assert (
        status == 202
    ), f"Expected NEW_PASSWORD_REQUIRED (202) on first login of new user; got {status}"
    chal = parse_body(first_login)
    assert chal["challenge"] == "NEW_PASSWORD_REQUIRED"
    assert "session" in chal
    session = chal["session"]

    # Reset password
    new_pw = "TestPW1!"
    reset_event = make_event(
        "POST",
        "/auth/reset",
        body={"username": username, "session": session, "newPassword": new_pw},
    )
    reset_resp = _call_auth(reset_event)
    assert reset_resp["statusCode"] == 204

    # Second login must provide usable tokens
    final_login_event = make_event(
        "POST",
        "/auth/login",
        body={"username": username, "password": new_pw},
    )
    final_login = _call_auth(final_login_event)
    assert final_login["statusCode"] == 200
    body = parse_body(final_login)
    return {
        "user": body["user"],
        "token": body["accessToken"],
        "username": username,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Credential fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def admin_login() -> dict[str, Any]:
    admin_u = os.getenv("PYTEST_ADMIN_USERNAME")
    admin_p = os.getenv("PYTEST_ADMIN_PASSWORD")
    if not admin_u or not admin_p:
        raise RuntimeError(
            "Set PYTEST_ADMIN_USERNAME and PYTEST_ADMIN_PASSWORD to valid test admin user "
            "that logs in with 200 OK and has active accessToken"
        )
    return _force_success_login(admin_u, admin_p)


@pytest.fixture(scope="session")
def user_login() -> dict[str, Any]:
    u = os.getenv("PYTEST_USER_USERNAME")
    p = os.getenv("PYTEST_USER_PASSWORD")
    if not u or not p:
        raise RuntimeError(
            "Set PYTEST_USER_USERNAME and PYTEST_USER_PASSWORD for a normal user "
            "that logs in with 200 OK and WITHOUT challenge"
        )
    return _force_success_login(u, p)


# ──────────────────────────────────────────────────────────────────────────────
# Managed User fixture: fully establishes new account + login flow
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def managed_user(admin_login) -> Generator[dict[str, Any], None, None]:
    admin_token = admin_login["accessToken"]

    username = f"user_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": username,
        "name": "New User",
        "phone": "+15550007777",
        "role": "user",
        # "preferences": {"foo": "bar"},  # Temporarily remove to avoid schema issues
    }
    resp = _call_user(
        make_event("POST", "/user", headers=_auth_header(admin_token), body=payload)
    )
    assert resp["statusCode"] == 201
    new = parse_body(resp)

    result = _force_user_established(new["username"], new["tempPassword"])
    uid = result["user"]
    token = result["token"]

    yield {"uid": uid, "username": username, "userToken": token}

    _call_user(make_event("DELETE", f"/user/{uid}", headers=_auth_header(admin_token)))


# ──────────────────────────────────────────────────────────────────────────────
# List Users
# ──────────────────────────────────────────────────────────────────────────────


def test_list_users_admin_ok(admin_login):
    token = admin_login["accessToken"]
    resp = _call_user(make_event("GET", "/user", headers=_auth_header(token)))
    assert resp["statusCode"] == 200


def test_list_users_forbidden_user(user_login):
    token = user_login["accessToken"]
    resp = _call_user(make_event("GET", "/user", headers=_auth_header(token)))
    assert resp["statusCode"] == 403


# ──────────────────────────────────────────────────────────────────────────────
# Get User
# ──────────────────────────────────────────────────────────────────────────────


def test_get_user_admin_ok(managed_user, admin_login):
    uid = managed_user["uid"]
    token = admin_login["accessToken"]
    resp = _call_user(make_event("GET", f"/user/{uid}", headers=_auth_header(token)))
    assert resp["statusCode"] == 200


def test_get_user_self_ok(managed_user):
    uid = managed_user["uid"]
    token = managed_user["userToken"]
    resp = _call_user(make_event("GET", f"/user/{uid}", headers=_auth_header(token)))
    assert resp["statusCode"] == 200


def test_get_user_forbidden_other_user(user_login, managed_user):
    uid = managed_user["uid"]
    token = user_login["accessToken"]
    resp = _call_user(make_event("GET", f"/user/{uid}", headers=_auth_header(token)))
    assert resp["statusCode"] == 403


# ──────────────────────────────────────────────────────────────────────────────
# Update User
# ──────────────────────────────────────────────────────────────────────────────


def test_update_user_admin_ok(managed_user, admin_login):
    uid = managed_user["uid"]
    token = admin_login["accessToken"]
    resp = _call_user(
        make_event(
            "PATCH",
            f"/user/{uid}",
            headers=_auth_header(token),
            body={"name": "Updated Name"},
        )
    )
    assert resp["statusCode"] == 200


def test_update_user_self_ok(managed_user):
    uid = managed_user["uid"]
    token = managed_user["userToken"]
    resp = _call_user(
        make_event(
            "PATCH",
            f"/user/{uid}",
            headers=_auth_header(token),
            body={"name": "My Name"},
        )
    )
    assert resp["statusCode"] == 200


def test_update_user_forbidden_not_self_not_admin(user_login, managed_user):
    uid = managed_user["uid"]
    token = user_login["accessToken"]
    resp = _call_user(
        make_event(
            "PATCH", f"/user/{uid}", headers=_auth_header(token), body={"name": "Nope"}
        )
    )
    assert resp["statusCode"] == 403


# ──────────────────────────────────────────────────────────────────────────────
# Password Update
# ──────────────────────────────────────────────────────────────────────────────


def test_update_password_admin_ok(managed_user, admin_login):
    uid = managed_user["uid"]
    token = admin_login["accessToken"]
    resp = _call_user(
        make_event(
            "PATCH",
            f"/user/{uid}/password",
            headers=_auth_header(token),
            body={"newPassword": "BetterPW1!"},
        )
    )
    assert resp["statusCode"] == 204


def test_update_password_self_requires_current(managed_user):
    uid = managed_user["uid"]
    token = managed_user["userToken"]
    resp = _call_user(
        make_event(
            "PATCH",
            f"/user/{uid}/password",
            headers=_auth_header(token),
            body={"newPassword": "ValidPass123!"},
        )
    )
    assert resp["statusCode"] == 403


# ──────────────────────────────────────────────────────────────────────────────
# Delete User
# ──────────────────────────────────────────────────────────────────────────────


def test_delete_user_forbidden_non_admin(user_login, managed_user):
    uid = managed_user["uid"]
    token = user_login["accessToken"]
    resp = _call_user(make_event("DELETE", f"/user/{uid}", headers=_auth_header(token)))
    assert resp["statusCode"] == 403


def test_delete_user_admin_ok(managed_user, admin_login):
    uid = managed_user["uid"]
    token = admin_login["accessToken"]
    resp = _call_user(make_event("DELETE", f"/user/{uid}", headers=_auth_header(token)))
    assert resp["statusCode"] == 204
