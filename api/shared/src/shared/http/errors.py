from http import HTTPStatus
from typing import Any

from pydantic import BaseModel

from .responses import Response

__all__ = [
    "ClientError",
    "Unauthorized",
    "Forbidden",
    "TooManyRequests",
    "ServerError",
    "InternalServerError",
]


class Problem(BaseModel):
    type: str | None = None
    title: str | None = None
    status: int | None = None
    detail: str | None = None
    instance: str | None = None
    parameters: dict[str, Any] = {}


# 4xx Client Errors


class ClientError(Response[Problem]):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        detail: str | None = None,
        *,
        type: str | None = None,
        title: str | None = None,
        instance: str | None = None,
        **parameters,
    ):
        super().__init__(
            Problem(
                type=type or "about:blank",
                title=title or self.status_code.phrase,
                status=self.status_code.value,
                detail=detail,
                instance=instance,
                parameters=parameters,
            )
        )


class Unauthorized(ClientError):
    status_code = HTTPStatus.UNAUTHORIZED


class Forbidden(ClientError):
    status_code = HTTPStatus.FORBIDDEN


class TooManyRequests(ClientError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS


# 5xx Server Errors


class ServerError(Exception, Response[Problem]):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        detail: str | None = None,
        *,
        type: str | None = None,
        title: str | None = None,
        instance: str | None = None,
        **parameters,
    ):
        super().__init__(
            Problem(
                type=type or "about:blank",
                title=title or self.status_code.phrase,
                status=self.status_code.value,
                detail=detail,
                instance=instance,
                parameters=parameters,
            )
        )


class InternalServerError(ServerError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
