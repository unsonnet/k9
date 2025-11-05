from __future__ import annotations

import uuid
import pytest
from typing import Generator, Any
from tests.utils.events import make_event, parse_body
from tests.utils.handlers import call_handler
from tests.utils.auth import force_user_established


def _auth(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def managed_user(admin_login) -> Generator[dict[str, Any], None, None]:
    admin_token = admin_login["accessToken"]

    username = f"user_{uuid.uuid4().hex[:8]}"
    resp = call_handler(
        "user",
        make_event(
            "POST",
            "/user",
            headers=_auth(admin_token),
            body={
                "username": username,
                "name": "New User",
                "phone": "+15550007777",
                "role": "user",
            },
        ),
    )
    assert resp["statusCode"] == 201
    created = parse_body(resp)

    result = force_user_established(created["username"], created["temporaryPassword"])
    uid = result["user"]
    token = result["token"]

    yield {"uid": uid, "username": username, "userToken": token}

    call_handler(
        "user", make_event("DELETE", f"/user/{uid}", headers=_auth(admin_token))
    )
