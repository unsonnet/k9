from __future__ import annotations

from typing import Any, Callable, Dict

from handlers.auth import handle_auth
from handlers.product import handle_product
from handlers.report import handle_report
from handlers.search import handle_search
from handlers.user import handle_user
from utils.http import ApiError, response


RouteHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


def _route(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get("rawPath") or event.get("path", "")
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if not path or not method:
        raise ApiError("Invalid event")
    # Top-level routers
    if path.startswith("/auth"):
        return handle_auth(event)
    if path.startswith("/product"):
        return handle_product(event)
    if path.startswith("/report"):
        return handle_report(event)
    if path.startswith("/search"):
        return handle_search(event)
    if path.startswith("/user"):
        return handle_user(event)
    return response(404, {"code": "NotFound", "message": "Unknown route"})


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        return _route(event)
    except ApiError as e:
        return e.to_response()
    except Exception as e:  # noqa: BLE001
        return response(500, {"code": "InternalServerError", "message": str(e)})
