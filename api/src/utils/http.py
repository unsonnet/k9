from __future__ import annotations

import json
from typing import Any, Dict, Optional


class ApiError(Exception):
    status_code: int = 500
    code: str = "InternalServerError"

    def __init__(self, message: Optional[str] = None):
        super().__init__(message or self.code)
        self.message = message or self.code

    def to_response(self) -> Dict[str, Any]:
        return response(self.status_code, {"error": {"code": self.code, "message": self.message}})


class InvalidRequest(ApiError):
    status_code = 400
    code = "InvalidRequest"


class Unauthorized(ApiError):
    status_code = 401
    code = "Unauthorized"


class Forbidden(ApiError):
    status_code = 403
    code = "Forbidden"


class NotFound(ApiError):
    status_code = 404
    code = "NotFound"


class Gone(ApiError):
    status_code = 410
    code = "Gone"


def response(status: int, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    return {
        "statusCode": status,
        "headers": hdrs,
        "body": json.dumps(body) if body is not None else "",
    }


def no_content() -> Dict[str, Any]:
    return response(204)
