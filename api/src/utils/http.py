#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
import traceback
from typing import Any, Generic, Mapping, TypeVar, TypedDict
from typing_extensions import Self
import cgi
from io import BytesIO

from .errors import DomainError

T_co = TypeVar("T_co", covariant=True)

# ──────────────────────────────────────────────
# Core response types
# ──────────────────────────────────────────────


class ErrorBody(TypedDict):
    code: str
    message: str
    traceback: str | None


@dataclass(slots=True, frozen=True)
class HttpResponse(Generic[T_co]):
    """Base typed HTTP response."""

    body: T_co | None = None
    status: int = 200
    headers: dict[str, str] | None = None

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(status={self.status}, body={self.body!r})"

    def to_apigw(self) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.headers:
            headers.update(self.headers)
        body = "" if self.body is None else json.dumps(self.body, default=_json_default)
        return {"statusCode": self.status, "headers": headers, "body": body}


# Success 2xx
@dataclass(slots=True, frozen=True)
class OK(HttpResponse[T_co]):
    status: int = 200


@dataclass(slots=True, frozen=True)
class Created(HttpResponse[T_co]):
    status: int = 201


@dataclass(slots=True, frozen=True)
class Accepted(HttpResponse[T_co]):
    status: int = 202


@dataclass(slots=True, frozen=True)
class NoContent(HttpResponse[None]):
    body: None = None
    status: int = 204


# Error 4xx/5xx
class HttpError(Exception):
    code: str = "Error"
    status: int = 500
    headers: dict[str, str] | None = None
    body: ErrorBody

    def __init__(self, msg: str | None = None) -> None:
        super().__init__(msg or self.code)
        self.body = ErrorBody(
            code=self.code,
            message=msg or self.code,
            traceback=None,
        )

    @classmethod
    def from_exception(cls, e: BaseException) -> Self:
        self = cls(f"{type(e).__name__}: {str(e)}")
        e = e.__cause__ if isinstance(e, DomainError) and e.__cause__ else e
        self.body["traceback"] = "".join(
            traceback.format_exception(type(e), e, e.__traceback__)
        )
        return self

    def to_apigw(self) -> dict[str, Any]:
        return {
            "statusCode": self.status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(self.body),
        }


# 4xx
class BadRequest(HttpError):
    code, status = "InvalidRequest", 400


class Unauthorized(HttpError):
    code, status = "Unauthorized", 401


class Forbidden(HttpError):
    code, status = "Forbidden", 403


class NotFound(HttpError):
    code, status = "NotFound", 404


class Conflict(HttpError):
    code, status = "Conflict", 409


class Gone(HttpError):
    code, status = "Gone", 410


class TooManyRequests(HttpError):
    code, status = "TooManyRequests", 429


# 5xx
class InternalServerError(HttpError):
    code, status = "InternalServerError", 500


# ──────────────────────────────────────────────
# Expanded helpers (safe parsing, path, and serialization)
# ──────────────────────────────────────────────

# Only allow safe URL path characters (RFC3986 pchar + '/')
_SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._~!$&'()*+,;=:@/\\-]*$")


def normalize_path(event: Mapping[str, Any]) -> str:
    """
    Return a sanitized, normalized path from API Gateway v1/v2 events.
      - Prefer v2 'rawPath' then v1 'path'
      - Ensure leading slash
      - Collapse duplicate slashes
      - Reject '..' segments
      - Enforce conservative character allowlist
    """
    raw = (
        (event.get("rawPath") if isinstance(event, dict) else None)
        or (event.get("path") if isinstance(event, dict) else None)
        or ""
    )
    if not isinstance(raw, str):
        raw = str(raw or "")
    if not raw.startswith("/"):
        raw = "/" + raw
    while "//" in raw:
        raw = raw.replace("//", "/")
    segs = [s for s in raw.split("/") if s not in ("", ".")]
    if any(s == ".." for s in segs):
        return "/"
    safe = "/".join([""] + segs)  # re-add leading slash
    if not _SAFE_PATH_RE.fullmatch(safe):
        return "/"
    return safe


def get_method(event: Mapping[str, Any]) -> str:
    """Return HTTP method from API Gateway v2 or v1."""
    if not isinstance(event, dict):
        return ""
    return (
        (event.get("requestContext", {}).get("http", {}) or {}).get("method")
        or event.get("httpMethod")
        or ""
    ).upper()


def read_json_body(event: Mapping[str, Any]) -> dict[str, Any]:
    """Safely parse a JSON request body (supports base64-encoded payloads)."""
    if not isinstance(event, dict):
        return {}
    raw: Any = event.get("body")

    if raw and event.get("isBase64Encoded"):
        try:
            raw = base64.b64decode(raw)
            try:
                raw = raw.decode("utf-8")
            except Exception:
                return {}
        except Exception:
            return {}

    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except Exception:
            return {}

    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}


def read_query(event: Mapping[str, Any]) -> dict[str, str]:
    """Return query string parameters as a dict of strings."""
    if not isinstance(event, dict):
        return {}
    qs = event.get("queryStringParameters") or {}
    return {str(k): str(v) for k, v in qs.items()} if isinstance(qs, dict) else {}


def read_bearer_token(event: Mapping[str, Any]) -> str | None:
    """Extract Bearer token from Authorization header (case-insensitive)."""
    if not isinstance(event, dict):
        return None
    headers = event.get("headers") or {}
    if not isinstance(headers, dict):
        return None
    auth = headers.get("Authorization") or headers.get("authorization")
    if not auth:
        return None
    if auth.startswith("Bearer "):
        return auth[7:]
    return auth


def read_multipart_body(
    event: Mapping[str, Any],
) -> dict[str, tuple[str | None, bytes]]:
    """
    Parse multipart/form-data from an API Gateway v1/v2 proxy event.

    Returns: { field_name: (filename_or_None, bytes_value) }
      - File parts => (filename, raw bytes)
      - Text parts => (None, raw bytes)  (empty string => b"")
    """
    if not isinstance(event, dict):
        raise BadRequest("Invalid event")

    headers = event.get("headers") or {}
    if not isinstance(headers, dict):
        headers = {}
    # case-insensitive header lookup
    hdrs = {str(k).lower(): v for k, v in headers.items()}
    ctype = hdrs.get("content-type") or hdrs.get("content_type") or ""
    if not isinstance(ctype, str) or "multipart/form-data" not in ctype:
        raise BadRequest("Content-Type must be multipart/form-data")

    body = event.get("body")
    if body is None:
        raise BadRequest("Missing body")

    # API Gateway may base64-encode the raw bytes
    try:
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(body)
        else:
            raw = body.encode("utf-8") if isinstance(body, str) else body
            if not isinstance(raw, (bytes, bytearray)):
                raise ValueError("Body must be bytes or string")
    except Exception:
        raise BadRequest("Invalid multipart body")

    # cgi.FieldStorage expects a WSGI-ish environ
    environ = {
        "REQUEST_METHOD": "POST",
        "CONTENT_TYPE": ctype,
        "CONTENT_LENGTH": str(len(raw)),
    }
    fp = BytesIO(raw)
    form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

    out: dict[str, tuple[str | None, bytes]] = {}

    # FieldStorage can be dict-like or a single item; normalize to a list
    items = []
    if getattr(form, "list", None):
        items = form.list or []
    else:
        items = [form]

    for field in items:
        # Some libraries emit None-name fields; skip them
        name = getattr(field, "name", None)
        if not name:
            continue

        if getattr(field, "filename", None):
            # File part
            filename = field.filename
            data = field.file.read() if field.file else b""
            out[name] = (filename, data)
        else:
            # Text part (treat as raw bytes; empty is b"")
            val = field.value if hasattr(field, "value") else ""
            if isinstance(val, str):
                data = val.encode("utf-8")
            elif isinstance(val, (bytes, bytearray)):
                data = bytes(val)
            else:
                data = str(val).encode("utf-8")
            out[name] = (None, data)

    return out


def _json_default(o: Any) -> Any:
    """Best-effort JSON default for dataclasses / pydantic / objects."""
    try:
        # Pydantic v2
        return getattr(o, "model_dump")()
    except Exception:
        pass
    try:
        # Pydantic v1
        return getattr(o, "dict")()
    except Exception:
        pass
    try:
        return o.__dict__
    except Exception:
        return str(o)
