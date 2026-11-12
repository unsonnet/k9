from http import HTTPStatus
from types import NoneType, get_original_bases
from typing import ClassVar, TypeVar, get_args, get_origin

from aws_lambda_powertools.event_handler import Response as BaseResponse
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from pydantic import BaseModel

__all__ = [
    "Response",
    "OK",
    "Created",
    "Accepted",
    "NoContent",
]


class Response[T: BaseModel | None](BaseResponse[T]):
    status_code: ClassVar[HTTPStatus]
    content_type: ClassVar[str | None] = "application/json"
    __model__: ClassVar[TypeVar] = T

    def __init_subclass__(cls):
        super().__init_subclass__()
        for bT in get_original_bases(cls):
            b: type = get_origin(bT) or bT
            if issubclass(b, Response):
                T = b.__model__
                if T in b.__type_params__:
                    T = get_args(bT)[b.__type_params__.index(T)]
                cls.__model__ = T
                return

    def __init__(self, body: T = None):
        super().__init__(
            status_code=self.status_code.value,
            content_type=self.content_type,
            body=body,
        )

    @classmethod
    def _openapi(cls, body_type: type[T]) -> OpenAPIResponse:
        return {
            "description": cls.status_code.phrase,
            "content": {cls.content_type: {"schema": body_type.model_json_schema()}}
            if cls.content_type is not None and not issubclass(body_type, NoneType)
            else {},
        }


# ──── 2xx Success ─────────────────────────────────────────────────────────────────────


class OK[T: BaseModel | None](Response[T]):
    status_code = HTTPStatus.OK


class Created[T: BaseModel | None](Response[T]):
    status_code = HTTPStatus.CREATED


class Accepted[T: BaseModel | None](Response[T]):
    status_code = HTTPStatus.ACCEPTED


class NoContent(Response[None]):
    status_code = HTTPStatus.NO_CONTENT
    content_type = None
