from __future__ import annotations

import os
import pytest
from tests.utils.events import make_event, parse_body
from tests.utils.handlers import call_handler


def _login(username: str, password: str):
    event = make_event(
        "POST", "/auth/login", body={"username": username, "password": password}
    )
    resp = call_handler("auth", event)
    return resp, parse_body(resp)


@pytest.fixture(scope="session")
def admin_login():
    u = os.getenv("PYTEST_ADMIN_USERNAME")
    p = os.getenv("PYTEST_ADMIN_PASSWORD")
    if not u or not p:
        raise RuntimeError("Admin creds missing")
    resp, body = _login(u, p)
    assert resp["statusCode"] == 200
    return body


@pytest.fixture(scope="session")
def user_login():
    u = os.getenv("PYTEST_USER_USERNAME")
    p = os.getenv("PYTEST_USER_PASSWORD")
    if not u or not p:
        raise RuntimeError("User creds missing")
    resp, body = _login(u, p)
    assert resp["statusCode"] == 200
    return body
