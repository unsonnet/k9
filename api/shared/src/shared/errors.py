from typing import Never


def assert_unreachable(_: Never) -> Never:
    raise TypeError(f"Unexpected type: {type(_).__name__}")


class DomainError(Exception): ...


class DomainInvalidCredentials(DomainError): ...


class DomainInvalidTokens(DomainError): ...


class DomainUserNotFound(DomainError): ...


class DomainUserNotConfirmed(DomainError): ...


class DomainRateLimited(DomainError): ...


class DomainExpiredToken(DomainError): ...


class DomainInvariantViolation(DomainError): ...


class DomainUnknown(DomainError): ...
