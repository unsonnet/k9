from __future__ import annotations

import json
import re
from typing import Any, Dict

from services.service import ReportsService
from utils.auth import get_auth_claims
from utils.http import InvalidRequest, Unauthorized, no_content, response


svc = ReportsService()


def handle_report(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get("rawPath") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get("httpMethod")
    claims = get_auth_claims(event, expected_typ="access")
    user_id = claims.get("sub") or claims.get("username") or claims.get("cognito:username")
    if not isinstance(user_id, str) or not user_id:
        raise Unauthorized("Missing user id in token")

    # parse path
    m = re.fullmatch(r"/report(?:/([0-9a-fA-F-]+)(?:/favorite/(?:([0-9a-fA-F-]+)))?)?", path)
    if not m:
        raise InvalidRequest("Invalid report route")
    rid, fav_pid = m.groups()

    # query params
    qp = event.get("queryStringParameters") or {}
    if path == "/report" and method == "GET":
        limit = int(qp.get("limit", "25"))
        next_token = qp.get("nextToken")
        everyone = qp.get("everyone", "false").lower() == "true"
        items, nt = svc.list(user_id, limit, next_token, everyone)
        return response(200, {"total": len(items), "nextToken": nt, "reports": items})

    body = json.loads((event.get("body") or "{}"))
    if path == "/report" and method == "POST":
        title = body.get("title")
        reference = body.get("reference")
        if not title or not reference:
            raise InvalidRequest("title and reference required")
        item = svc.create(user_id, title, reference)
        return response(201, item)

    if rid and not fav_pid:
        if method == "GET":
            item = svc.get(rid)
            return response(200, item)
        if method == "PATCH":
            updates = {k: v for k, v in body.items() if k in ("title", "reference")}
            item = svc.update(rid, updates)
            return response(200, item)
        if method == "DELETE":
            svc.delete(rid)
            return no_content()

    if rid and fav_pid:
        if method == "PUT":
            svc.favorite(rid, fav_pid, add=True)
            return no_content()
        if method == "DELETE":
            svc.favorite(rid, fav_pid, add=False)
            return no_content()

    raise InvalidRequest("Unsupported report route")
