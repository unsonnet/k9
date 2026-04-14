from http import HTTPStatus
from types import NoneType
from typing import ClassVar

from aws_lambda_powertools.event_handler import Response as BaseResponse
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from pydantic import BaseModel

__all__ = [
    "Response",
    "OK",
    "Accepted",
    "NoContent",
]


class Response[T: BaseModel | None](BaseResponse[T]):
    status_code: ClassVar[HTTPStatus]
    content_type: ClassVar[str] = "application/json"

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
            if not issubclass(body_type, NoneType)
            else {},
        }


# 2xx Success


class OK[T: BaseModel](Response[T]):
    status_code = HTTPStatus.OK


class Accepted[T: BaseModel](Response[T]):
    status_code = HTTPStatus.ACCEPTED


class NoContent(Response[None]):
    status_code = HTTPStatus.NO_CONTENT


# 3xx Redirection
