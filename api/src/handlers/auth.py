from __future__ import annotations

from typing import Any, Mapping

from utils.http import BadRequest, HttpResponse, OK, read_bearer_token, read_json_body
from utils.routing import Router
from models.auth import (
    AuthContext,
    ForgotRequest,
    LoginRequest,
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
    return OK(svc.login(req))


@router.route("/refresh", method="POST")
def refresh(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = RefreshRequest.model_validate(data)
    return OK(svc.refresh(req))


@router.route("/forgot", method="POST")
def forgot(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = ForgotRequest.model_validate(data)
    return OK(svc.forgot(req))


@router.route("/reset", method="POST")
def reset(event: Mapping[str, Any]) -> HttpResponse[Any]:
    data = read_json_body(event)
    req = ResetRequest.model_validate(data)
    return OK(svc.reset(req))


@router.route("/logout", method="POST")
def logout(event: Mapping[str, Any]) -> HttpResponse[Any]:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return OK(svc.logout(AuthContext(bearerToken=token)))


def lambda_handler(event, context):
    return router.dispatch(event)
