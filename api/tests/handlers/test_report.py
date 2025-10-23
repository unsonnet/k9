from __future__ import annotations

from uuid import uuid4

import pytest

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import report as h

    return h.lambda_handler(event, None)


def test_list_reports_ok(auth_headers):
    event = make_event(
        "GET", "/report", headers=auth_headers, query={"limit": "5", "everyone": "true"}
    )
    resp = _call(event)
    # Initially empty list is OK
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert set(body.keys()) >= {"total", "reports"}


def test_create_get_update_delete_report_flow(auth_headers, store):
    # Need a product for reference
    from tests.fakes.providers import FakeProductDBProvider
    from src.models.product import Name
    from src.models.auth import AuthContext

    pdb = FakeProductDBProvider(store)
    prod = pdb.post_product(
        AuthContext(bearerToken="seed-token-1234567890"),
        name=Name(brand="b"),
        category={},
    )

    # Create
    create = make_event(
        "POST",
        "/report",
        headers=auth_headers,
        body={"title": "R1", "reference": str(prod.id)},
    )
    created = _call(create)
    assert created["statusCode"] == 201
    rid = parse_body(created)["id"]

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
    assert parse_body(updr)["title"] == "R2"

    # Favorite product
    fav = make_event("PUT", f"/report/{rid}/favorite/{prod.id}", headers=auth_headers)
    favr = _call(fav)
    assert favr["statusCode"] in (200, 204)

    # Unfavorite product
    unfav = make_event(
        "DELETE", f"/report/{rid}/favorite/{prod.id}", headers=auth_headers
    )
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
