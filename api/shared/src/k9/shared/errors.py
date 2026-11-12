from typing import Never


class DomainError(Exception): ...


class DomainForbidden(DomainError): ...


class DomainInvariantViolation(DomainError): ...


class DomainNotFound(DomainError): ...


class DomainRateLimited(DomainError): ...


class DomainUnauthorized(DomainError): ...


class DomainUnknown(DomainError): ...


def assert_unreachable(_: Never) -> Never:
    raise DomainInvariantViolation(f"Unexpected type: {type(_).__name__}")


# ──── Unauthorized specific errors ────────────────────────────────────────────────────


class DomainExpiredToken(DomainUnauthorized): ...


class DomainInvalidCredentials(DomainUnauthorized): ...


class DomainInvalidTokens(DomainUnauthorized): ...


# ──── Config specific errors ──────────────────────────────────────────────────────────


class MissingSettingError(RuntimeError):
    def __init__(self, *keys: str):
        variables = ", ".join(keys)
        super().__init__(f"Missing required environment setting. Checked: {variables}")
