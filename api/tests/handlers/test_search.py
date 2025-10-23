from __future__ import annotations

import pytest

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import search as h

    return h.lambda_handler(event, None)


@pytest.mark.xfail(
    reason="Search providers not implemented; awaiting backend implementation"
)
def test_search_ok(auth_headers):
    event = make_event(
        "POST",
        "/search",
        headers=auth_headers,
        query={"limit": "5", "partial": "true"},
        body={"name": {"brand": "b"}},
    )
    resp = _call(event)
    assert resp["statusCode"] == 200


def test_search_missing_auth():
    event = make_event("POST", "/search", body={})
    resp = _call(event)
    assert resp["statusCode"] == 400
