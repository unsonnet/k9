#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Generic, TypeVar, TypedDict

T_co = TypeVar("T_co", covariant=True)


# ──────────────────────────────────────────────
# Common structures
# ──────────────────────────────────────────────


class ErrorBody(TypedDict):
    code: str
    message: str


@dataclass(slots=True, frozen=True)
class HttpResponse(Generic[T_co]):
    """Base typed HTTP response."""

    body: T_co | None = None
    status: int = 200
    headers: dict[str, str] | None = None

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(status={self.status}, body={self.body!r})"


# ──────────────────────────────────────────────
# Success 2xx
# ──────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class OK(HttpResponse[T_co]):
    status: int = 200


@dataclass(slots=True, frozen=True)
class Created(HttpResponse[T_co]):
    status: int = 201


@dataclass(slots=True, frozen=True)
class Accepted(HttpResponse[T_co]):
    status: int = 202


@dataclass(slots=True, frozen=True)
class NoContent(HttpResponse[None]):
    body: None = None
    status: int = 204


# ──────────────────────────────────────────────
# Error 4xx/5xx
# ──────────────────────────────────────────────


class HttpError(HttpResponse[ErrorBody], Exception):
    """Base mixin for all errors."""

    code: str = "Error"
    status: int = 500

    def __init__(self, message: str | None = None) -> None:
        body = ErrorBody(code=self.code, message=message or self.code)
        HttpResponse.__init__(self, body=body, status=self.status)
        Exception.__init__(self, body["message"])


# 4xx client errors
class BadRequest(HttpError):
    code, status = "InvalidRequest", 400


class Unauthorized(HttpError):
    code, status = "Unauthorized", 401


class Forbidden(HttpError):
    code, status = "Forbidden", 403


class NotFound(HttpError):
    code, status = "NotFound", 404


class Conflict(HttpError):
    code, status = "Conflict", 409


class Gone(HttpError):
    code, status = "Gone", 410


# 5xx server errors
class InternalServerError(HttpError):
    code, status = "InternalServerError", 500
