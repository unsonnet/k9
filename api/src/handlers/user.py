from __future__ import annotations

import json
import re
from typing import Any, Dict

from models.api import CreateUserRequest, PasswordUpdateRequest, UpdateUserRequest
from services.service import UsersService
from utils.auth import get_auth_claims
from utils.http import Forbidden, InvalidRequest, Unauthorized, no_content, response


svc = UsersService()


def handle_user(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get("rawPath") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get("httpMethod")
    claims = get_auth_claims(event, expected_typ="access")
    # Simple role check: expecting claim 'role' (Cognito custom claim or local token)
    role = claims.get("role", "user")

    m = re.fullmatch(r"/user(?:/([0-9a-fA-F-]+)(?:/(password))?)?", path)
    if not m:
        raise InvalidRequest("Invalid user route")
    uid, pw_kw = m.groups()

    qp = event.get("queryStringParameters") or {}
    if path == "/user" and method == "GET":
        if role != "admin":
            raise Forbidden("Insufficient permissions")
        limit = int(qp.get("limit", "25"))
        next_token = qp.get("nextToken")
        items, nt = svc.list(limit, next_token)
        return response(200, {"total": len(items), "nextToken": nt, "users": items})

    body = json.loads((event.get("body") or "{}"))
    if path == "/user" and method == "POST":
        if role != "admin":
            raise Forbidden("Insufficient permissions")
        req = CreateUserRequest.model_validate(body)
        item = svc.create(req.username, req.email, req.role, req.preferences)
        return response(201, item)

    if uid and not pw_kw:
        if method == "GET":
            item = svc.get(uid)
            return response(200, item)
        if method == "PATCH":
            req = UpdateUserRequest.model_validate(body)
            updates = req.model_dump(exclude_none=True)
            item = svc.update(uid, updates)
            return response(200, item)
        if method == "DELETE":
            if role != "admin":
                raise Forbidden("Insufficient permissions")
            svc.delete(uid)
            return no_content()

    if uid and pw_kw == "password" and method == "PATCH":
        _ = PasswordUpdateRequest.model_validate(body)  # validation only; not stored here
        # In a real system, verify current password and update in IdP
        return no_content()

    raise InvalidRequest("Unsupported user route")
