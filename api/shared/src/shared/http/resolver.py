from dataclasses import dataclass
from functools import wraps
from http import HTTPStatus
from inspect import signature
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
    Mapping,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response as BaseResponse
from aws_lambda_powertools.event_handler.api_gateway import (
    _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
)
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestValidationError,
)
from pydantic import ValidationError as PydanticValidationError
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse

from shared.errors import DomainInvalidTokens

from .errors import (
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    ServerError,
    UnprocessableEntity,
)
from .responses import Response


@dataclass(frozen=True)
class Caller:
    id: str
    name: str
    email: str
    groups: tuple[str, ...]


class HttpResolver(APIGatewayHttpResolver):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("enable_validation", True)
        super().__init__(*args, **kwargs)
        super().exception_handler(RequestValidationError)(
            lambda e: UnprocessableEntity(cause=e)
        )
        super().exception_handler(PydanticValidationError)(
            lambda e: UnprocessableEntity(cause=e)
        )
        super().exception_handler(NotFoundError)(self._handle_routing_error)
        super().exception_handler(ServerError)(lambda e: e)
        super().exception_handler(Exception)(lambda e: InternalServerError(cause=e))

    # ──── Auth Context ────

    def claims(self) -> Mapping[str, Any]:
        try:
            return self.current_event.request_context.authorizer["jwt"]["claims"]
        except (AttributeError, KeyError, TypeError) as exc:
            raise DomainInvalidTokens("Missing JWT claims") from exc

    @staticmethod
    def _groups(claims: Mapping[str, Any]) -> tuple[str, ...]:
        match claims.get("cognito:groups", ()):
            case str() as value:
                return tuple(
                    group.strip() for group in value.split(",") if group.strip()
                )
            case list() | tuple() as values:
                return tuple(str(group) for group in values)
            case _:
                return ()

    def caller(self) -> Caller:
        claims = self.claims()

        try:
            user_id = str(claims["sub"])
        except KeyError as exc:
            raise DomainInvalidTokens("Missing subject claim") from exc

        return Caller(
            id=user_id,
            name=str(claims.get("username") or claims.get("cognito:username") or ""),
            email=str(claims.get("email") or ""),
            groups=self._groups(claims),
        )

    def _handle_routing_error(self, exc: NotFoundError) -> NotFound | MethodNotAllowed:
        method = self.current_event.http_method.upper()
        path = self._remove_prefix(self.current_event.path)
        registered_routes = self._static_routes + self._dynamic_routes

        if any(
            route.method != method and route.rule.match(path)
            for route in registered_routes
        ):
            return MethodNotAllowed(cause=exc)

        return NotFound(cause=exc)

    # ──── Routes ────

    def route[T: Callable[..., Any]](  # type: ignore[override]
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[T], T]:
        def decorator(func: T) -> T:
            parsed_responses = self._parse(func, responses or {})
            normalized_func = self._normalize(func)

            return super(HttpResolver, self).route(
                rule,
                method,
                cors,
                compress,
                cache_control,
                summary,
                description,
                parsed_responses,
                response_description,
                tags,
                operation_id,
                include_in_schema,
                security,
                openapi_extensions,
                deprecated,
                enable_validation,
                custom_response_validation_http_code,
                middlewares,
            )(normalized_func)

        return decorator

    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        return super().put(*args, **kwargs)

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def patch(self, *args, **kwargs):
        return super().patch(*args, **kwargs)

    # ──── OpenAPI Response Parsing ────

    @classmethod
    def _parse(
        cls,
        func: Callable[..., Any],
        responses: dict[int, str | OpenAPIResponse],
    ) -> dict[int, OpenAPIResponse] | None:
        result: dict[int, OpenAPIResponse] = {}

        annotation = get_type_hints(func, include_extras=True).get("return")

        for response_cls, body_type in cls._extract(annotation):
            result[response_cls.status_code.value] = response_cls._openapi(body_type)

        for status, value in responses.items():
            if isinstance(value, str):
                result.setdefault(status, {})["description"] = value
            else:
                result[status] = value

        return result or None

    @classmethod
    def _body(cls, response_cls: type[Response[Any]]) -> type[Any]:
        meta = getattr(response_cls, "__pydantic_generic_metadata__", None)
        args = meta.get("args", ()) if meta else ()
        if args:
            return args[0]

        for candidate in (response_cls, *response_cls.__mro__[1:]):
            if not isinstance(candidate, type):
                continue

            for base in getattr(candidate, "__orig_bases__", ()):
                origin = get_origin(base)
                if origin is None or not isinstance(origin, type):
                    continue
                if not issubclass(origin, Response):
                    continue

                args = get_args(base)
                if args:
                    return args[0]

            meta = getattr(candidate, "__pydantic_generic_metadata__", None)
            args = meta.get("args", ()) if meta else ()
            if args:
                return args[0]

        return NoneType

    @classmethod
    def _extract(
        cls,
        annotation: Any,
    ) -> list[tuple[type[Response[Any]], type[Any]]]:
        if annotation is None:
            return []

        origin = get_origin(annotation)

        if origin is Union or origin is UnionType:
            result: list[tuple[type[Response[Any]], type[Any]]] = []
            for arg in get_args(annotation):
                result.extend(cls._extract(arg))
            return result

        if (
            origin is not None
            and isinstance(origin, type)
            and issubclass(origin, Response)
        ):
            args = get_args(annotation)
            body_type = args[0] if args else NoneType
            return [(origin, body_type)]

        if isinstance(annotation, type) and issubclass(annotation, Response):
            return [(annotation, cls._body(annotation))]

        return []

    @classmethod
    def _union(cls, annotation: Any) -> Any:
        all_body_types = [body_type for _, body_type in cls._extract(annotation)]
        has_none = any(bt is NoneType for bt in all_body_types)
        body_types = [bt for bt in all_body_types if bt is not NoneType]

        if not body_types:
            return NoneType

        union = body_types[0]
        for body_type in body_types[1:]:
            union = union | body_type

        if has_none:
            union = union | NoneType
        return union

    @classmethod
    def _normalize[T: Callable[..., Any]](cls, func: T) -> T:
        original_annotation = get_type_hints(func, include_extras=True).get("return")
        normalized_return = BaseResponse[cls._union(original_annotation)]
        sig = signature(func).replace(return_annotation=normalized_return)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            return func(*args, **kwargs)

        wrapper.__signature__ = sig  # type: ignore[attr-defined]
        wrapper.__annotations__ = dict(getattr(func, "__annotations__", {}))
        wrapper.__annotations__["return"] = normalized_return
        setattr(wrapper, "__original_return_annotation__", original_annotation)

        return wrapper  # type: ignore[return-value]
