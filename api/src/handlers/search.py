from __future__ import annotations

from typing import Any, Mapping

from utils.http import OK, BadRequest, read_bearer_token, read_json_body, read_query
from utils.routing import Router
from models.domain.auth import AuthContext
from models.api.search import SearchParams, SearchRequest
from services.search import SearchService

router = Router(prefix="/search")
svc = SearchService()


def _ctx(event: Mapping[str, Any]) -> AuthContext:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return AuthContext(bearer_token=token)


@router.route("", method="POST")
def search(event: Mapping[str, Any]) -> OK[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    qp = read_query(event)
    filters = SearchRequest.model_validate(data)
    params = SearchParams(
        limit=int(qp["limit"]) if qp.get("limit") else None,
        next_token=qp.get("nextToken"),
        include_partial_matches=(qp.get("partial", "false").lower() == "true"),
    )
    return OK(svc.search(ctx, params, filters))


def lambda_handler(event, context):
    return router.dispatch(event)
