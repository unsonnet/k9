from __future__ import annotations

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import search as h

    return h.lambda_handler(event, None)


def test_search_ok(auth_headers, store, monkeypatch):
    # Seed a product that search will return
    from tests.fakes.providers import FakeProductDBProvider, FakeSearchProvider
    from src.models.product import Name
    from src.models.auth import AuthContext

    pdb = FakeProductDBProvider(store)
    prod = pdb.post_product(
        AuthContext(bearerToken="seed-token-1234567890"),
        name=Name(brand="b", model="m"),
        category={},
    )

    # Point search provider at the seeded product
    from src.handlers import search as h_search

    h_search.svc.provider = FakeSearchProvider([prod.id])

    event = make_event(
        "POST",
        "/search",
        headers=auth_headers,
        query={"limit": "5", "partial": "true"},
        body={"name": {"brand": "b"}},
    )
    resp = _call(event)
    assert resp["statusCode"] == 200
    body = parse_body(resp)
    assert set(body.keys()) >= {"total", "results"}
    assert body["total"] == 1
    assert body["results"][0]["id"] == str(prod.id)


def test_search_missing_auth():
    event = make_event("POST", "/search", body={})
    resp = _call(event)
    assert resp["statusCode"] == 400
