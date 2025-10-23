from __future__ import annotations

from uuid import uuid4

import pytest

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import report as h

    return h.lambda_handler(event, None)


@pytest.mark.xfail(
    reason="Report provider not implemented; awaiting backend implementation"
)
def test_list_reports_ok(auth_headers):
    event = make_event(
        "GET", "/report", headers=auth_headers, query={"limit": "5", "everyone": "true"}
    )
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    inner = body.get("body", body) if isinstance(body, dict) else body
    assert set(inner.keys()) >= {"total", "reports"}


@pytest.mark.xfail(
    reason="Report provider not implemented; awaiting backend implementation"
)
def test_create_get_update_delete_report_flow(auth_headers):
    rid = uuid4()
    pid = uuid4()
    # Create
    create = make_event(
        "POST",
        "/report",
        headers=auth_headers,
        body={"title": "R1", "reference": str(pid)},
    )
    created = _call(create)
    assert created["statusCode"] == 201
    # Get
    get = make_event("GET", f"/report/{rid}", headers=auth_headers)
    got = _call(get)
    assert got["statusCode"] == 200
    # Update
    upd = make_event(
        "PATCH", f"/report/{rid}", headers=auth_headers, body={"title": "R2"}
    )
    updr = _call(upd)
    assert updr["statusCode"] == 200
    # Favorite product
    fav = make_event("PUT", f"/report/{rid}/favorite/{pid}", headers=auth_headers)
    favr = _call(fav)
    assert favr["statusCode"] in (200, 204)
    # Unfavorite product
    unfav = make_event("DELETE", f"/report/{rid}/favorite/{pid}", headers=auth_headers)
    unfavr = _call(unfav)
    assert unfavr["statusCode"] in (200, 204)
    # Delete
    dele = make_event("DELETE", f"/report/{rid}", headers=auth_headers)
    delr = _call(dele)
    assert delr["statusCode"] == 204


def test_report_missing_auth():
    event = make_event("GET", "/report")
    resp = _call(event)
    assert resp["statusCode"] == 400
