import json
from typing import Dict, Any, Optional, Callable

import pytest

from src.utils.auth import create_token
from src.config import settings


def _build_event(path: str, method: str, *, headers: Optional[Dict[str, str]] = None, body: Optional[Any] = None, query: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
    }
    if headers:
        payload["headers"] = headers
    if query:
        payload["queryStringParameters"] = query
    if body is not None:
        if isinstance(body, (dict, list)):
            payload["body"] = json.dumps(body)
        elif isinstance(body, (bytes, bytearray)):
            payload["body"] = body.decode("utf-8")
        else:
            payload["body"] = str(body)
    return payload


@pytest.fixture()
def token_user() -> str:
    # deterministic subject for tests
    return create_token("00000000-0000-0000-0000-000000000001", settings().access_token_ttl, token_type="access", extra={"role": "user"})


@pytest.fixture()
def token_admin() -> str:
    return create_token("00000000-0000-0000-0000-0000000000ad", settings().access_token_ttl, token_type="access", extra={"role": settings().admin_role})


@pytest.fixture()
def auth_header_user(token_user: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token_user}"}


@pytest.fixture()
def auth_header_admin(token_admin: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token_admin}"}


@pytest.fixture()
def make_event() -> Callable[..., Dict[str, Any]]:
    return _build_event


@pytest.fixture()
def create_product(auth_header_user: Dict[str, str]):
    def _create(name: Optional[Dict[str, str]] = None, category: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        payload = {
            "name": name or {"brand": "Acme", "series": "Series", "model": "M1"},
            "category": category or {"type": "tile", "material": "ceramic"},
        }
        from src.app import lambda_handler
        event = _build_event("/product", "POST", headers=auth_header_user, body=payload)
        res = lambda_handler(event, None)
        assert res["statusCode"] == 201, res
        return json.loads(res["body"])

    return _create


@pytest.fixture()
def png_base64() -> Callable[[int], str]:
    def _gen(size: int = 2) -> str:
        import base64
        import io
        from PIL import Image

        img = Image.new("RGB", (size, size), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    return _gen


@pytest.fixture(autouse=True)
def _reset_memdb():
    # Reset the in-memory database used by repositories to avoid test leakage
    try:
        from src.services import repositories as repos

        repos._MEM_DB.clear()
        repos._MEM_DB.update({"users": {}, "products": {}, "reports": {}})
    except Exception:
        pass
    yield
