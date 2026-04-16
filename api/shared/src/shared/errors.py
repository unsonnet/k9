from typing import Never


class DomainError(Exception): ...


class DomainExpiredToken(DomainError): ...


class DomainForbidden(DomainError): ...


class DomainInvalidCredentials(DomainError): ...


class DomainInvalidTokens(DomainError): ...


class DomainInvariantViolation(DomainError): ...


class DomainRateLimited(DomainError): ...


class DomainUnknown(DomainError): ...


class DomainUserNotConfirmed(DomainError): ...


class DomainUserNotFound(DomainError): ...


DomainUnauthorized = (
    DomainExpiredToken,
    DomainInvalidCredentials,
    DomainInvalidTokens,
    DomainUserNotConfirmed,
    DomainUserNotFound,
)


def assert_unreachable(_: Never) -> Never:
    raise DomainInvariantViolation(f"Unexpected type: {type(_).__name__}")
