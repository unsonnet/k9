from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from utils.routing import Router
from utils.http import (
    OK,
    Created,
    NoContent,
    BadRequest,
    read_json_body,
    read_bearer_token,
    read_query,
)
from models.common import AuthContext
from models.user import (
    CreateUserRequest,
    ListUsersParams,
    UpdateUserRequest,
    UpdatePasswordRequest,
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
def list_users(event: Mapping[str, Any]) -> OK[Any]:
    ctx = _ctx(event)
    qp = read_query(event)
    params = ListUsersParams(
        limit=int(qp["limit"]) if qp.get("limit") else None,
        nextToken=qp.get("nextToken"),
    )
    return OK(svc.list_users(ctx, params))


@router.route("", method="POST")
def create_user(event: Mapping[str, Any]) -> Created[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    req = CreateUserRequest.model_validate(data)
    return Created(svc.create_user(ctx, req))


@router.route("/{userId}", method="GET")
def get_user(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    return OK(svc.get_user(ctx, uid))


@router.route("/{userId}", method="PATCH")
def update_user(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    data = read_json_body(event)
    req = UpdateUserRequest.model_validate(data)
    return OK(svc.update_user(ctx, uid, req))


@router.route("/{userId}", method="DELETE")
def delete_user(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    svc.delete_user(ctx, uid)
    return NoContent()


@router.route("/{userId}/password", method="PATCH")
def update_password(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    uid = UUID(params["userId"])
    data = read_json_body(event)
    req = UpdatePasswordRequest.model_validate(data)
    return OK(svc.update_password(ctx, uid, req))


def lambda_handler(event, context):
    return router.dispatch(event)
