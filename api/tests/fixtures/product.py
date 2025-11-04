from __future__ import annotations

import base64
import numpy as np
import os
import struct
import pytest
from typing import Generator, Any
from tests.utils.events import make_event, make_multipart_event, parse_body
from tests.utils.handlers import call_handler


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _dummy_mask():
    raw = struct.pack(">II", 1, 1) + bytes([0b10000000])
    return base64.b64encode(raw).decode()


def _dummy_hom():
    arr = np.eye(3, dtype="<f4")
    return base64.b64encode(arr.tobytes()).decode()


@pytest.fixture
def managed_product(user_login, admin_login) -> Generator[dict[str, Any], None, None]:
    user_token = user_login["accessToken"]
    admin_token = admin_login["accessToken"]

    resp = call_handler(
        "product",
        make_event(
            "POST",
            "/product",
            headers=_auth_header(user_token),
            body={
                "name": {"brand": "Test", "model": "Z"},
                "category": {"type": "ceramic"},
            },
        ),
    )
    assert resp["statusCode"] == 201
    prod = parse_body(resp)
    pid = prod["id"]

    yield {
        "pid": pid,
        "product": prod,
        "userToken": user_token,
        "adminToken": admin_token,
    }

    call_handler(
        "product",
        make_event("DELETE", f"/product/{pid}", headers=_auth_header(admin_token)),
    )


@pytest.fixture
def managed_format(managed_product) -> Generator[dict[str, Any], None, None]:
    pid = managed_product["pid"]
    resp = call_handler(
        "product",
        make_event(
            "POST",
            f"/product/{pid}/format",
            headers=_auth_header(managed_product["userToken"]),
            body={"aspect": "matte"},
        ),
    )
    assert resp["statusCode"] == 201
    fmt = parse_body(resp)
    fid = fmt["id"]

    yield {**managed_product, "fid": fid}

    call_handler(
        "product",
        make_event(
            "DELETE",
            f"/product/{pid}/format/{fid}",
            headers=_auth_header(managed_product["adminToken"]),
        ),
    )


@pytest.fixture
def managed_vendor(managed_format) -> Generator[dict[str, Any], None, None]:
    pid = managed_format["pid"]
    fid = managed_format["fid"]
    user_token = managed_format["userToken"]
    admin_token = managed_format["adminToken"]

    # Create vendor
    resp = call_handler(
        "product",
        make_event(
            "POST",
            f"/product/{pid}/format/{fid}/vendor",
            headers=_auth_header(user_token),
            body={"sku": "TESTSKU", "store": "TestStore", "name": "VendorX"},
        ),
    )
    assert resp["statusCode"] == 201
    ven = parse_body(resp)
    vid = ven["id"]

    yield {**managed_format, "vid": vid}

    # Cleanup (admin required)
    call_handler(
        "product",
        make_event(
            "DELETE",
            f"/product/{pid}/format/{fid}/vendor/{vid}",
            headers=_auth_header(admin_token),
        ),
    )


@pytest.fixture
def managed_image(managed_product) -> Generator[dict[str, Any], None, None]:
    """
    Upload a test image for a product, yield pid + iid, and always clean up afterwards.
    Mask and hom are intentionally empty (no transformations).
    """
    from tests.utils.events import make_multipart_event, make_event, parse_body
    from tests.utils.handlers import call_handler
    import os

    pid = managed_product["pid"]
    user_token = managed_product["userToken"]
    admin_token = managed_product["adminToken"]

    img_path = os.getenv("PYTEST_DUMMY_IMAGE")
    if not img_path:
        raise RuntimeError("PYTEST_DUMMY_IMAGE is not set")

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    # Upload (POST /product/{pid}/image)
    event = make_multipart_event(
        "POST",
        f"/product/{pid}/image",
        headers=_auth_header(user_token),
        fields={
            "image": ("dummy.jpg", img_bytes),
            "mask": (None, None),
            "hom": (None, None),
        },
    )
    resp = call_handler("product", event)
    assert resp["statusCode"] == 201

    body = parse_body(resp)
    assert isinstance(body, dict)
    assert "id" in body, "Expected POST /product/{pid}/image to return Image.id"
    iid = body["id"]

    yield {**managed_product, "iid": iid}

    # Cleanup (DELETE /product/{pid}/image/{iid}), requires admin
    delete_resp = call_handler(
        "product",
        make_event(
            "DELETE",
            f"/product/{pid}/image/{iid}",
            headers=_auth_header(admin_token),
        ),
    )
    assert delete_resp["statusCode"] == 204
