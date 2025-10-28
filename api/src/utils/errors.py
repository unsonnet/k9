#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Consolidated domain error definitions used by service and provider layers.

These exceptions represent business/domain semantics and are intentionally
decoupled from transport concerns (HTTP). Service classes map these errors
to typed HTTP responses in utils.http.
"""

from __future__ import annotations


# ──────────────────────────────────────────────────────────────────────────────
# Base Domain Error
# ──────────────────────────────────────────────────────────────────────────────
class DomainError(Exception):
    """Base class for all domain-level errors."""


# ──────────────────────────────────────────────────────────────────────────────
# Generic / Common Errors
# ──────────────────────────────────────────────────────────────────────────────
class DomainUnauthorized(DomainError):
    """Operation requires authentication or lacks valid credentials."""


class DomainForbidden(DomainError):
    """Authenticated but not permitted to perform the operation."""


class DomainNotFound(DomainError):
    """Requested resource was not found in the domain layer."""


class DomainConflict(DomainError):
    """Resource state conflicts with the requested operation."""


class DomainInvariantViolation(DomainError):
    """A domain invariant was violated (unexpected or illegal state)."""


# ──────────────────────────────────────────────────────────────────────────────
# Auth-Specific Domain Errors
# ──────────────────────────────────────────────────────────────────────────────
class DomainInvalidCredentials(DomainError):
    """Authentication failed due to invalid credentials."""


class DomainExpiredToken(DomainError):
    """Token, session, or verification code is expired or invalid."""


class DomainUserDisabled(DomainError):
    """User account is disabled, locked, or not verified."""


class DomainRateLimited(DomainError):
    """Request rate exceeded — caller should retry later."""


# ──────────────────────────────────────────────────────────────────────────────
# Exports
# ──────────────────────────────────────────────────────────────────────────────
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
    "DomainUserDisabled",
    "DomainRateLimited",
]
