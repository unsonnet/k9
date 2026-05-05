from http import HTTPStatus
from typing import Any

from aws_lambda_powertools import Logger
from pydantic import BaseModel

from .responses import Response

__all__ = [
    "ClientError",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "TooManyRequests",
    "ServerError",
    "InternalServerError",
]


LOG = Logger()


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
        cause: Exception | None = None,
        type_: str | None = None,
        title: str | None = None,
        instance: str | None = None,
        **parameters,
    ):
        super().__init__(
            payload := Problem(
                type=type_ or "about:blank",
                title=title or self.status_code.phrase,
                status=self.status_code.value,
                detail=detail,
                instance=instance,
                parameters=parameters,
            )
        )

        if cause is not None:
            LOG.error(
                payload.title,
                exc_info=(type(cause), cause, cause.__traceback__),
            )


class BadRequest(ClientError):
    status_code = HTTPStatus.BAD_REQUEST


class Unauthorized(ClientError):
    status_code = HTTPStatus.UNAUTHORIZED


class Forbidden(ClientError):
    status_code = HTTPStatus.FORBIDDEN


class NotFound(ClientError):
    status_code = HTTPStatus.NOT_FOUND


class TooManyRequests(ClientError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS


# 5xx Server Errors


class ServerError(Response[Problem], Exception):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        detail: str | None = None,
        *,
        cause: Exception | None = None,
        type_: str | None = None,
        title: str | None = None,
        instance: str | None = None,
        **parameters,
    ):
        super().__init__(
            payload := Problem(
                type=type_ or "about:blank",
                title=title or self.status_code.phrase,
                status=self.status_code.value,
                detail=detail,
                instance=instance,
                parameters=parameters,
            )
        )

        if cause is not None:
            LOG.error(
                payload.title,
                exc_info=(type(cause), cause, cause.__traceback__),
            )


class InternalServerError(ServerError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
