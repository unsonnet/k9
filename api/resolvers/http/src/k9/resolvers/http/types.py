from http import HTTPStatus
from inspect import Parameter
from typing import Any, Callable, NotRequired, Protocol, TypedDict, overload

from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from k9.types.common import Caller
from pydantic import BaseModel

__all__ = [
    "CALLER_PARAM",
    "HttpRouteDecorator",
    "HttpRouteOptions",
]


CALLER_PARAM = Parameter(
    name="caller",
    kind=Parameter.POSITIONAL_OR_KEYWORD,
    annotation=Caller,
)


class HttpRouteOptions(TypedDict):
    cors: NotRequired[bool]
    compress: NotRequired[bool]
    cache_control: NotRequired[str]
    summary: NotRequired[str]
    description: NotRequired[str]
    responses: NotRequired[dict[int, str | OpenAPIResponse]]
    response_description: NotRequired[str]
    tags: NotRequired[list[str]]
    operation_id: NotRequired[str]
    include_in_schema: NotRequired[bool]
    security: NotRequired[list[dict[str, list[str]]]]
    openapi_extensions: NotRequired[dict[str, Any]]
    deprecated: NotRequired[bool]
    enable_validation: NotRequired[bool]
    custom_response_validation_http_code: NotRequired[int | HTTPStatus]
    middlewares: NotRequired[list[Callable[..., Any]]]


class HttpRouteDecorator[R: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    @overload
    def __call__(self, func: Callable[[Caller], T]) -> Callable[[Caller], T]: ...
    @overload
    def __call__(self, func: Callable[[Caller, R], T]) -> Callable[[Caller, R], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...
