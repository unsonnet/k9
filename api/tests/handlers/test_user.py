from __future__ import annotations

import json
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


def test_list_users_ok(auth_headers, store):
    # seed two users via provider fake
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    ctx = AuthContext(bearerToken="seed-token-1234567890")
    provider.post_user(ctx, username="alice", role="admin", preferences=None)
    provider.post_user(ctx, username="bob", role="viewer", preferences={"x": "y"})

    event = make_event("GET", "/user", headers=auth_headers, query={"limit": "10"})
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert "total" in body and "users" in body
    assert isinstance(body["users"], list)
    assert body["total"] == len(body["users"]) >= 2


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
    assert set(body.keys()) == {"id", "username", "role", "preferences"}
    assert body["username"] == "charlie"


def test_create_user_conflict(auth_headers, store):
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="dupe",
        role="viewer",
        preferences=None,
    )

    event = make_event(
        "POST",
        "/user",
        headers=auth_headers,
        body={"username": "dupe", "role": "viewer"},
    )
    resp = _call(event)
    assert resp["statusCode"] == 409


def test_get_user_ok(auth_headers, store):
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    created = provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="eve",
        role="viewer",
        preferences=None,
    )

    event = make_event("GET", f"/user/{created.id}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert body["id"] == str(created.id)


def test_get_user_not_found(auth_headers):
    event = make_event("GET", f"/user/{uuid4()}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 404


def test_update_user_ok(auth_headers, store):
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    created = provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="frank",
        role="viewer",
        preferences={"a": "b"},
    )

    event = make_event(
        "PATCH",
        f"/user/{created.id}",
        headers=auth_headers,
        body={"username": "frankie", "preferences": {"a": None, "c": "d"}},
    )
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert body["username"] == "frankie"
    assert "a" not in body["preferences"] and body["preferences"]["c"] == "d"


def test_delete_user_ok(auth_headers, store):
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    created = provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="gina",
        role="viewer",
        preferences=None,
    )

    event = make_event("DELETE", f"/user/{created.id}", headers=auth_headers)
    resp = _call(event)
    assert resp["statusCode"] == 204


def test_update_password_forbidden(auth_headers, store):
    from tests.fakes.providers import FakeUserDBProvider
    from src.models.auth import AuthContext

    provider = FakeUserDBProvider(store)
    created = provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="harry",
        role="viewer",
        preferences=None,
    )

    event = make_event(
        "PATCH",
        f"/user/{created.id}/password",
        headers=auth_headers,
        body={"currentPassword": "wrong", "newPassword": "newpass123"},
    )
    resp = _call(event)
    assert resp["statusCode"] == 403
