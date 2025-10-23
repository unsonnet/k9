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
    """Build a minimal API Gateway v2-like event for Router.dispatch.

    - Sets requestContext.http.method and rawPath
    - Supports JSON body serialization
    - Accepts optional headers and queryStringParameters
    """
    event: dict[str, Any] = {
        "requestContext": {"http": {"method": method.upper()}},
        "rawPath": path,
        "headers": {**(headers or {})},
        "queryStringParameters": {**(query or {})} if query else None,
        "isBase64Encoded": False,
    }
    if body is None:
        event["body"] = None
    elif isinstance(body, (str, bytes)):
        event["body"] = body.decode() if isinstance(body, bytes) else body
    else:
        event["body"] = json.dumps(body)
    return event


def parse_body(resp: Mapping[str, Any]) -> Any:
    """Parse JSON body from API Gateway style response; return None on empty."""
    body = resp.get("body")
    if not body:
        return None
    try:
        return json.loads(body)
    except Exception:
        return body
