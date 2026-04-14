from functools import wraps
from http import HTTPStatus
from inspect import signature
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
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
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse

from .errors import InternalServerError
from .responses import Response


class HttpResolver(APIGatewayHttpResolver):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("enable_validation", True)
        super().__init__(*args, **kwargs)
        super().exception_handler(Exception)(lambda e: InternalServerError(str(e)))

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

    def post(self, *args, **kwargs):  # type: ignore[override]
        return super().post(*args, **kwargs)

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
            meta = getattr(annotation, "__pydantic_generic_metadata__", None)
            if meta:
                args = meta.get("args", ())
                origin = meta.get("origin") or annotation
                body_type = args[0] if args else NoneType
                return [(origin, body_type)]

            return [(annotation, NoneType)]

        return []

    @classmethod
    def _union(cls, annotation: Any) -> Any:
        body_types = [
            body_type
            for _, body_type in cls._extract(annotation)
            if body_type is not NoneType
        ]

        if not body_types:
            return NoneType

        union = body_types[0]
        for body_type in body_types[1:]:
            union = union | body_type
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
