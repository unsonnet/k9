from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from utils.http import (
    HttpResponse,
    BadRequest,
    read_bearer_token,
    read_json_body,
    read_query,
)
from utils.routing import Router
from models.auth import AuthContext
from models.user import (
    CreateUserRequest,
    ListUsersParams,
    UpdatePasswordRequest,
    UpdateUserRequest,
)
from services.user.service import UserService

router = Router(prefix="/user")
svc = UserService()


def _ctx(event: Mapping[str, Any]) -> AuthContext:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return AuthContext(bearerToken=token)


@router.route("", method="GET")
def list_users(event: Mapping[str, Any]) -> HttpResponse[Any]:
    ctx = _ctx(event)
    qp = read_query(event)
    params = ListUsersParams(
        limit=int(qp["limit"]) if qp.get("limit") else None,
        nextToken=qp.get("nextToken"),
    )
    return svc.list_users(ctx, params)


@router.route("", method="POST")
def create_user(event: Mapping[str, Any]) -> HttpResponse[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    payload = CreateUserRequest.model_validate(data)
    return svc.create_user(ctx, payload)


@router.route("/{userId}", method="GET")
def get_user(event: Mapping[str, Any], params: Mapping[str, str]) -> HttpResponse[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    return svc.get_user(ctx, uid)


@router.route("/{userId}", method="PATCH")
def update_user(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    data = read_json_body(event)
    payload = UpdateUserRequest.model_validate(data)
    return svc.update_user(ctx, uid, payload)


@router.route("/{userId}", method="DELETE")
def delete_user(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    return svc.delete_user(ctx, uid)


@router.route("/{userId}/password", method="PATCH")
def update_password(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    data = read_json_body(event)
    payload = UpdatePasswordRequest.model_validate(data)
    return svc.update_password(ctx, uid, payload)


def lambda_handler(event, context):
    return router.dispatch(event)
