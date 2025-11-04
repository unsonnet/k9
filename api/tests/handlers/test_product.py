from __future__ import annotations

import base64
from tests.utils.events import make_event, parse_body
from tests.utils.handlers import call_handler


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_product_ok(user_login):
    resp = call_handler(
        "product",
        make_event(
            "POST",
            "/product",
            headers=_auth(user_login["accessToken"]),
            body={
                "name": {"brand": "B", "model": "M"},
                "category": {"type": "ceramic"},
            },
        ),
    )
    assert resp["statusCode"] == 201
    assert set(parse_body(resp)) == {"id", "name", "category", "formats", "images"}


def test_get_product_ok(managed_product):
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "GET", f"/product/{pid}", headers=_auth(managed_product["userToken"])
        ),
    )
    assert resp["statusCode"] == 200


def test_update_product_ok(managed_product):
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "PATCH",
            f"/product/{pid}",
            headers=_auth(managed_product["userToken"]),
            body={"name": {"brand": "Updated"}},
        ),
    )
    assert resp["statusCode"] == 200


def test_delete_product_forbidden_user(managed_product):
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "DELETE", f"/product/{pid}", headers=_auth(managed_product["userToken"])
        ),
    )
    assert resp["statusCode"] == 403


def test_create_format_ok(managed_product):
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "POST",
            f"/product/{pid}/format",
            headers=_auth(managed_product["userToken"]),
            body={"aspect": "glossy"},
        ),
    )
    assert resp["statusCode"] == 201


def test_update_format_ok(managed_format):
    pid = managed_format["pid"]
    fid = managed_format["fid"]
    resp = call_handler(
        "product",
        make_event(
            "PATCH",
            f"/product/{pid}/format/{fid}",
            headers=_auth(managed_format["userToken"]),
            body={"aspect": "updated"},
        ),
    )
    assert resp["statusCode"] == 200


def test_create_vendor_ok(managed_format):
    pid = managed_format["pid"]
    fid = managed_format["fid"]
    resp = call_handler(
        "product",
        make_event(
            "POST",
            f"/product/{pid}/format/{fid}/vendor",
            headers=_auth(managed_format["userToken"]),
            body={"sku": "SKU1", "store": "S1", "name": "VendorA"},
        ),
    )
    assert resp["statusCode"] == 201


def test_update_vendor_ok(managed_vendor):
    pid = managed_vendor["pid"]
    fid = managed_vendor["fid"]
    vid = managed_vendor["vid"]
    resp = call_handler(
        "product",
        make_event(
            "PATCH",
            f"/product/{pid}/format/{fid}/vendor/{vid}",
            headers=_auth(managed_vendor["userToken"]),
            body={"name": "VendorRenamed"},
        ),
    )
    assert resp["statusCode"] == 200


def test_upload_image_ok(managed_product):
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "POST",
            f"/product/{pid}/image",
            headers=_auth(managed_product["userToken"]),
            body={
                "image": base64.b64encode(b"img").decode(),
                "mask": managed_product.get("mask") or "",  # from fixtures if needed
                "hom": managed_product.get("hom") or "",
            },
        ),
    )
    assert resp["statusCode"] == 201


def test_update_image_ok(managed_image):
    pid = managed_image["pid"]
    iid = managed_image["iid"]
    resp = call_handler(
        "product",
        make_event(
            "PATCH",
            f"/product/{pid}/image/{iid}",
            headers=_auth(managed_image["userToken"]),
            body={"mask": base64.b64encode(b"xyz").decode()},
        ),
    )
    assert resp["statusCode"] == 200
