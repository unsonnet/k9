from __future__ import annotations

import base64
import json
from typing import Any, Mapping
from uuid import uuid4


# ---------------------------------------------------------------------
# Basic JSON event builder
# ---------------------------------------------------------------------
def make_event(
    method: str,
    path: str,
    *,
    body: Any | None = None,
    headers: Mapping[str, str] | None = None,
    query: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Construct a minimal API Gateway v2-like event (JSON requests)."""
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


# ---------------------------------------------------------------------
# Multipart helpers
# ---------------------------------------------------------------------
def _new_boundary() -> str:
    return f"----pytest{uuid4().hex}"


def build_multipart_body(
    fields: dict[str, tuple[str | None, bytes | None] | None],
    *,
    default_file_ct: str = "application/octet-stream",
) -> tuple[str, str]:
    """
    Build a multipart/form-data body suitable for API Gateway v2.

    :param fields:
        name -> None  -> skip part entirely
        name -> (filename, bytes) where:
            filename is None -> simple form field (text/binary)
            filename is str  -> "file" upload field
    """
    boundary = _new_boundary()
    parts: list[bytes] = []

    for name, entry in fields.items():
        if entry is None:
            continue  # explicit: do not include part

        filename, content = entry
        content = content or b""

        if filename is not None:
            # File upload part
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {default_file_ct}\r\n\r\n"
            ).encode()
        else:
            # Plain field part
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            ).encode()

        parts.append(header + content + b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode())
    raw = b"".join(parts)

    return base64.b64encode(raw).decode(), f"multipart/form-data; boundary={boundary}"


def make_multipart_event(
    method: str,
    path: str,
    *,
    fields: dict[str, tuple[str | None, bytes | None] | None],
    headers: Mapping[str, str] | None = None,
    query: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """
    Construct an API Gateway v2-like event carrying multipart/form-data.
    """
    body_b64, content_type = build_multipart_body(fields)

    return {
        "requestContext": {"http": {"method": method.upper()}},
        "rawPath": path,
        "headers": {**(headers or {}), "Content-Type": content_type},
        "queryStringParameters": {**(query or {})} if query else None,
        "isBase64Encoded": True,
        "body": body_b64,
    }
