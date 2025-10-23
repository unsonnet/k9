#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Consolidated domain error definitions used by service and provider layers.

These exceptions represent business/domain semantics and are intentionally
decoupled from transport concerns (HTTP). Service classes map these errors
to typed HTTP responses in utils.http.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain-level errors."""


class DomainUnauthorized(DomainError):
    """Operation requires authentication or lacks valid credentials."""


class DomainForbidden(DomainError):
    """Authenticated but not permitted to perform the operation."""


class DomainNotFound(DomainError):
    """Requested resource was not found in the domain layer."""


class DomainConflict(DomainError):
    """Resource state conflicts with the requested operation."""


class DomainInvariantViolation(DomainError):
    """A domain invariant was violated (unexpected/illegal state)."""


# Auth-specific domain errors
class DomainInvalidCredentials(DomainError):
    """Auth-specific: provided credentials are invalid."""


class DomainExpiredToken(DomainError):
    """Auth-specific: token is expired or otherwise invalid."""


__all__ = [
    # base
    "DomainError",
    # generic
    "DomainUnauthorized",
    "DomainForbidden",
    "DomainNotFound",
    "DomainConflict",
    "DomainInvariantViolation",
    # auth-specific
    "DomainInvalidCredentials",
    "DomainExpiredToken",
]
