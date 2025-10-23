from __future__ import annotations

from uuid import uuid4

import pytest

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import user as h

    return h.lambda_handler(event, None)


def test_list_users_missing_auth():
    event = make_event("GET", "/user", query={"limit": "10"})
    resp = _call(event)
    assert resp["statusCode"] == 400  # handler raises BadRequest for missing header


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_list_users_ok(auth_headers):
    event = make_event("GET", "/user", headers=auth_headers, query={"limit": "10"})
    resp = _call(event)
    assert resp["statusCode"] == 200


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_create_user_ok(auth_headers):
    payload = {
        "username": "charlie",
        "role": "editor",
        "preferences": {"theme": "dark"},
    }
    event = make_event("POST", "/user", headers=auth_headers, body=payload)
    resp = _call(event)
    assert resp["statusCode"] == 201
    body = parse_body(resp)
    # Handler double-wraps service responses; unwrap if present
    inner = body.get("body", body) if isinstance(body, dict) else body
    assert set(inner.keys()) >= {"id", "username", "role", "preferences"}
    assert inner["username"] == "charlie"


@pytest.mark.xfail(reason="User provider not implemented; conflict path unavailable")
def test_create_user_conflict(auth_headers):
    event = make_event(
        "POST",
        "/user",
        headers=auth_headers,
        body={"username": "dupe", "role": "viewer"},
    )
    resp = _call(event)
    assert resp["statusCode"] == 409


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_get_user_ok(auth_headers):
    event = make_event("GET", f"/user/{uuid4()}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 200


@pytest.mark.xfail(
    reason="User provider not implemented; will surface as 500 until implemented"
)
def test_get_user_not_found(auth_headers):
    event = make_event("GET", f"/user/{uuid4()}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 404


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_update_user_ok(auth_headers):
    event = make_event(
        "PATCH",
        f"/user/{uuid4()}",
        headers=auth_headers,
        body={"username": "frankie", "preferences": {"a": None, "c": "d"}},
    )
    resp = _call(event)
    assert resp["statusCode"] == 200


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_delete_user_ok(auth_headers):
    event = make_event("DELETE", f"/user/{uuid4()}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 204


@pytest.mark.xfail(
    reason="User provider not implemented; awaiting backend implementation"
)
def test_update_password_forbidden(auth_headers):
    event = make_event(
        "PATCH",
        f"/user/{uuid4()}/password",
        headers=auth_headers,
        body={"currentPassword": "wrong", "newPassword": "newpass123"},
    )
    resp = _call(event)
    assert resp["statusCode"] == 403
