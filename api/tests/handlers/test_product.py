from __future__ import annotations

import base64
from uuid import uuid4

import pytest

from tests.utils.events import make_event, parse_body


def _call(event):
    from src.handlers import product as h

    return h.lambda_handler(event, None)


@pytest.mark.xfail(
    reason="Product provider not implemented; awaiting backend implementation"
)
def test_create_product_ok(auth_headers):
    payload = {
        "name": {"brand": "b", "series": "s", "model": "m"},
        "category": {"type": "tile"},
    }
    event = make_event("POST", "/product", headers=auth_headers, body=payload)
    resp = _call(event)
    assert resp["statusCode"] == 201
    body = parse_body(resp)
    # Handler double-wraps service responses; unwrap if present
    inner = body.get("body", body) if isinstance(body, dict) else body
    assert set(inner.keys()) >= {"id", "name", "category", "formats", "images"}


@pytest.mark.xfail(
    reason="Product provider not implemented; awaiting backend implementation"
)
def test_get_update_delete_product_flow(auth_headers):
    # Create
    create = make_event(
        "POST",
        "/product",
        headers=auth_headers,
        body={"name": {"brand": "b"}, "category": {"k": "v"}},
    )
    created = _call(create)
    pid = parse_body(created)["id"]

    # Get
    get = make_event("GET", f"/product/{pid}", headers=auth_headers)
    got = _call(get)
    assert got["statusCode"] == 200

    # Update (patch name/category semantics)
    upd = make_event(
        "PATCH",
        f"/product/{pid}",
        headers=auth_headers,
        body={"name": {"series": "sx"}, "category": {"k": None, "k2": "v2"}},
    )
    updr = _call(upd)
    assert updr["statusCode"] == 200
    body = parse_body(updr)
    inner = body.get("body", body) if isinstance(body, dict) else body
    assert inner["name"]["series"] == "sx"
    assert "k" not in inner["category"] and inner["category"]["k2"] == "v2"

    # Delete
    dele = make_event("DELETE", f"/product/{pid}", headers=auth_headers)
    delr = _call(dele)
    assert delr["statusCode"] == 204


@pytest.mark.xfail(
    reason="Product provider not implemented; awaiting backend implementation"
)
def test_format_and_vendor_crud(auth_headers):
    # Create product first
    created = _call(
        make_event(
            "POST",
            "/product",
            headers=auth_headers,
            body={"name": {"brand": "b"}, "category": {}},
        )
    )
    pid = parse_body(created)["id"]

    # Create format
    fmt_create = make_event(
        "POST",
        f"/product/{pid}/format",
        headers=auth_headers,
        body={"aspect": "rect", "length": {"value": 10, "unit": "cm"}},
    )
    fmt_resp = _call(fmt_create)
    assert fmt_resp["statusCode"] == 201
    fid = parse_body(fmt_resp)["id"]

    # Update format
    fmt_update = make_event(
        "PATCH",
        f"/product/{pid}/format/{fid}",
        headers=auth_headers,
        body={"width": {"value": 5, "unit": "cm"}},
    )
    fmt_upd_resp = _call(fmt_update)
    assert fmt_upd_resp["statusCode"] == 200

    # Create vendor
    v_create = make_event(
        "POST",
        f"/product/{pid}/format/{fid}/vendor",
        headers=auth_headers,
        body={
            "sku": "SKU1",
            "store": "S",
            "name": "N",
            "price": {"value": 100, "unit": "USD"},
        },
    )
    v_resp = _call(v_create)
    assert v_resp["statusCode"] == 201
    vid = parse_body(v_resp)["id"]

    # Update vendor
    v_update = make_event(
        "PATCH",
        f"/product/{pid}/format/{fid}/vendor/{vid}",
        headers=auth_headers,
        body={"discontinued": True},
    )
    v_upd_resp = _call(v_update)
    assert v_upd_resp["statusCode"] == 200

    # Delete vendor
    v_del = make_event(
        "DELETE", f"/product/{pid}/format/{fid}/vendor/{vid}", headers=auth_headers
    )
    v_del_resp = _call(v_del)
    assert v_del_resp["statusCode"] == 204

    # Delete format
    fmt_del = make_event("DELETE", f"/product/{pid}/format/{fid}", headers=auth_headers)
    fmt_del_resp = _call(fmt_del)
    assert fmt_del_resp["statusCode"] == 204


@pytest.mark.xfail(
    reason="Product provider not implemented; awaiting backend implementation"
)
def test_image_upload_update_delete(auth_headers):
    # Create product first
    created = _call(
        make_event(
            "POST",
            "/product",
            headers=auth_headers,
            body={"name": {"brand": "b"}, "category": {}},
        )
    )
    pid = parse_body(created)["id"]

    # Upload image
    payload = {
        "image": base64.b64encode(b"img").decode(),
        "mask": "mask-data",
        "hom": "hom-data",
    }
    up = make_event("POST", f"/product/{pid}/image", headers=auth_headers, body=payload)
    upr = _call(up)
    assert upr["statusCode"] == 201
    img = parse_body(upr)
    iid = img["id"]
    assert img["url"].startswith("https://example.com/")

    # Update image metadata
    ip = make_event(
        "PATCH",
        f"/product/{pid}/image/{iid}",
        headers=auth_headers,
        body={"mask": "m2"},
    )
    ipr = _call(ip)
    assert ipr["statusCode"] == 200

    # Delete image
    idel = make_event("DELETE", f"/product/{pid}/image/{iid}", headers=auth_headers)
    idelr = _call(idel)
    assert idelr["statusCode"] == 204


def test_requires_auth_negative():
    # Missing Authorization header on protected endpoints should 400 per current handler
    event = make_event("GET", "/product/00000000-0000-0000-0000-000000000000")
    resp = _call(event)
    assert resp["statusCode"] == 400
