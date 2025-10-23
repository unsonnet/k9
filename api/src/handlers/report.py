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
from models.report import (
    CreateReportRequest,
    UpdateReportRequest,
    ListReportsParams,
)
from services.report.service import ReportService

router = Router(prefix="/report")
svc = ReportService()


def _ctx(event: Mapping[str, Any]) -> AuthContext:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return AuthContext(bearerToken=token)


@router.route("", method="GET")
def list_reports(event: Mapping[str, Any]) -> OK[Any]:
    ctx = _ctx(event)
    qp = read_query(event)
    params = ListReportsParams(
        limit=int(qp["limit"]) if qp.get("limit") else None,
        nextToken=qp.get("nextToken"),
        everyone=(qp.get("everyone", "false").lower() == "true"),
    )
    return OK(svc.list_reports(ctx, params))


@router.route("", method="POST")
def create_report(event: Mapping[str, Any]) -> Created[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    req = CreateReportRequest.model_validate(data)
    return Created(svc.create_report(ctx, req))


@router.route("/{reportId}", method="GET")
def get_report(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    rid = UUID(params["reportId"])
    return OK(svc.get_report(ctx, rid))


@router.route("/{reportId}", method="PATCH")
def update_report(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    rid = UUID(params["reportId"])
    data = read_json_body(event)
    req = UpdateReportRequest.model_validate(data)
    return OK(svc.update_report(ctx, rid, req))


@router.route("/{reportId}", method="DELETE")
def delete_report(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    rid = UUID(params["reportId"])
    svc.delete_report(ctx, rid)
    return NoContent()


@router.route("/{reportId}/favorite/{productId}", method="PUT")
def favorite_product(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    rid = UUID(params["reportId"])
    pid = UUID(params["productId"])
    return OK(svc.favorite_product(ctx, rid, pid))


@router.route("/{reportId}/favorite/{productId}", method="DELETE")
def unfavorite_product(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    rid = UUID(params["reportId"])
    pid = UUID(params["productId"])
    return OK(svc.unfavorite_product(ctx, rid, pid))


def lambda_handler(event, context):
    return router.dispatch(event)
