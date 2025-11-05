from __future__ import annotations

import os
from tests.utils.events import make_event, make_multipart_event, parse_body
from tests.utils.handlers import call_handler
from tests.fixtures.product import _dummy_mask, _dummy_hom  # helpers kept, now binary


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_product_ok(managed_product):
    prod = managed_product["product"]
    assert set(prod) == {"id", "name", "category", "formats", "images"}
    assert prod["name"]["brand"] == "Test"
    assert prod["name"]["model"] == "Z"
    assert prod["category"]["type"] == "ceramic"


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


def test_upload_image_ok(managed_image):
    # fixture already performed an upload and validated 201 response
    assert managed_image["iid"]


def test_update_image_ok(managed_image):
    """
    Update mask via multipart using a bit-packed mask that matches the actual dummy image dimensions.
    """
    pid = managed_image["pid"]
    iid = managed_image["iid"]
    token = managed_image["userToken"]

    img_path = os.getenv("PYTEST_DUMMY_IMAGE")
    assert img_path, "PYTEST_DUMMY_IMAGE not set"

    mask_bytes = _dummy_mask(img_path)  # binary payload: [>II][packbits]
    hom_bytes = _dummy_hom()  # binary payload: [>9f]

    event = make_multipart_event(
        "PATCH",
        f"/product/{pid}/image/{iid}",
        headers=_auth(token),
        fields={
            "mask": ("mask.bin", mask_bytes),
            "hom": ("hom.bin", hom_bytes),
        },
    )
    resp = call_handler("product", event)
    assert resp["statusCode"] == 200
