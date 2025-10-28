from __future__ import annotations

import re
from inspect import signature
from typing import Any, Callable, Mapping

from utils.http import (
    HttpResponse,
    HttpError,
    NotFound,
    InternalServerError,
    get_method,
    normalize_path,
)

# Types
RouteKey = tuple[str, str]  # (METHOD, canonical path template like /auth/login)
Handler = Callable[..., HttpResponse[Any]]

_PARAM_RE = re.compile(r"{([A-Za-z_][A-Za-z0-9_]*)}")  # {param}
_SEGMENT_RE = r"(?P<%s>[^/]+)"


class Router:
    """
    Minimal, framework-free router with path-parameter support.

    Usage:
        router = Router(prefix="/auth")  # optional
        @router.route("/login", method="POST")
        def login(event, params): ...
        def lambda_handler(event, context): return router.dispatch(event)
    """

    def __init__(self, prefix: str = "") -> None:
        self._prefix = self._canonical(prefix)
        self._routes: dict[RouteKey, Handler] = {}
        self._compiled: dict[tuple[str, str], tuple[re.Pattern[str], Handler]] = {}

    @staticmethod
    def _canonical(path: str) -> str:
        path = path or "/"
        if not path.startswith("/"):
            path = "/" + path
        # collapse slashes
        while "//" in path:
            path = path.replace("//", "/")
        # strip trailing slash except root
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return path

    @staticmethod
    def _compile_template(template: str) -> re.Pattern[str]:
        """
        Convert '/thing/{id}/child/{childId}' → regex with named groups.
        """

        def repl(m: re.Match[str]) -> str:
            name = m.group(1)
            return _SEGMENT_RE % name

        regex = "^" + _PARAM_RE.sub(repl, template) + "$"
        return re.compile(regex)

    def route(self, path: str, method: str = "GET") -> Callable[[Handler], Handler]:
        """
        Decorator to register a route. Supports {param} segments.
        Handlers may be defined as `def f(event)` or `def f(event, params)`.
        """
        method_u = method.upper()
        full = self._canonical(self._prefix + (path or ""))
        key = (method_u, full)

        def decorator(func: Handler) -> Handler:
            self._routes[key] = func
            self._compiled[key] = (self._compile_template(full), func)
            return func

        return decorator

    def dispatch(self, event: Mapping[str, Any]) -> dict[str, Any]:
        """
        Find & invoke a handler. Returns an API Gateway proxy response.
        """
        try:
            method = get_method(event)
            path = normalize_path(event)
            if not method:
                raise NotFound("Missing HTTP method")
            # Try exact or compiled matches
            for (mtd, tmpl), (rx, func) in self._compiled.items():
                if mtd != method:
                    continue
                m = rx.match(path)
                if m:
                    params = m.groupdict()
                    return self._invoke(func, event, params)
            raise NotFound(f"Route not found: {method} {path}")
        except HttpError as e:
            return e.to_apigw()
        except Exception as e:  # pragma: no cover
            return InternalServerError(str(e)).to_apigw()

    def _invoke(
        self, func: Handler, event: Mapping[str, Any], params: Mapping[str, str]
    ) -> dict[str, Any]:
        """
        Call handler with (event) or (event, params) depending on its signature.
        """
        try:
            sig = signature(func)
            if len(sig.parameters) >= 2:
                result = func(event, params)  # type: ignore[misc]
            else:
                result = func(event)
            if not isinstance(result, HttpResponse):
                raise InternalServerError("Handler did not return HttpResponse")
            return result.to_apigw()
        except HttpError as e:
            return e.to_apigw()
