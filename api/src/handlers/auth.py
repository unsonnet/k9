from __future__ import annotations

import json
from typing import Any, Dict

from models.api import ForgotRequest, LoginRequest, RefreshRequest, ResetRequest
from services.service import AuthService
from utils.http import InvalidRequest, no_content, response


svc = AuthService()


def handle_auth(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get("rawPath") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get("httpMethod")
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = bytes(body, "utf-8").decode("utf-8")
    data = json.loads(body or "{}")

    if path.endswith("/login") and method == "POST":
        req = LoginRequest.model_validate(data)
        tokens = svc.login(req.email, req.password)
        return response(200, tokens.model_dump(mode="json"))
    if path.endswith("/refresh") and method == "POST":
        req = RefreshRequest.model_validate(data)
        tokens = svc.refresh(req.refreshToken)
        return response(200, tokens.model_dump(mode="json"))
    if path.endswith("/forgot") and method == "POST":
        req = ForgotRequest.model_validate(data)
        svc.forgot(req.email)
        return no_content()
    if path.endswith("/reset") and method == "POST":
        req = ResetRequest.model_validate(data)
        svc.reset(str(req.user), req.session, req.newPassword)
        return no_content()
    if path.endswith("/logout") and method == "POST":
        # Stateless JWT: client discards token; optional blacklist could be implemented
        return no_content()

    raise InvalidRequest("Unsupported auth route")
