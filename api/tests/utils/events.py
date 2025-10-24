from __future__ import annotations
import json
from typing import Any, Mapping


def make_event(
    method: str,
    path: str,
    *,
    body: Any | None = None,
    headers: Mapping[str, str] | None = None,
    query: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Construct a minimal API Gateway v2-like event."""
    event: dict[str, Any] = {
        "requestContext": {"http": {"method": method.upper()}},
        "rawPath": path,
        "headers": {**(headers or {})},
        "queryStringParameters": {**(query or {})} if query else None,
        "isBase64Encoded": False,
        "body": None,
    }
    if body is not None:
        event["body"] = (
            body.decode()
            if isinstance(body, bytes)
            else body if isinstance(body, str) else json.dumps(body)
        )
    return event


def parse_body(resp: Mapping[str, Any]) -> Any:
    """Return parsed JSON body or None if empty/non-JSON."""
    body = resp.get("body")
    if not body:
        return None
    try:
        return json.loads(body)
    except Exception:
        return body
