from __future__ import annotations

import base64
import numpy as np
import struct
import pytest
from typing import Generator, Any
from tests.utils.events import make_event, parse_body
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

    yield {"pid": pid, "userToken": user_token, "adminToken": admin_token}

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
