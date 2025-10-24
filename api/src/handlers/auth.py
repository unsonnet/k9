from __future__ import annotations

from typing import Any, Mapping

from utils.http import (
    Unauthorized,
    HttpResponse,
    read_json_body,
)
from utils.routing import Router
from models.auth import (
    AuthContext,
    ForgetRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetRequest,
)
from services.auth.service import AuthService

router = Router(prefix="/auth")
svc = AuthService()


@router.route("/login", method="POST")
def login(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = LoginRequest.model_validate(data)
    return svc.login(req)


@router.route("/refresh", method="POST")
def refresh(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = RefreshRequest.model_validate(data)
    return svc.refresh(req)


@router.route("/forget", method="POST")
def forget(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = ForgetRequest.model_validate(data)
    return svc.forget(req)


@router.route("/reset", method="POST")
def reset(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = ResetRequest.model_validate(data)
    return svc.reset(req)


@router.route("/logout", method="POST")
def logout(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = LogoutRequest.model_validate(data)
    return svc.logout(req)


def lambda_handler(event, context):
    return router.dispatch(event)
