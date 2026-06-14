import re
from typing import Final

# ──── Session ─────────────────────────────────────────────────────────────────────────


_SESSION_MIN: Final = 20
_SESSION_MAX: Final = 2048


def validate_session(session: str) -> str:
    if not _SESSION_MIN <= len(session) <= _SESSION_MAX:
        raise ValueError(f"session must be {_SESSION_MIN}-{_SESSION_MAX} characters")
    return session


# ──── Token ───────────────────────────────────────────────────────────────────────────


_TOKEN_MIN: Final = 1
_TOKEN_MAX: Final = 131072
_TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9-_=.]+$")


def validate_token(token: str) -> str:
    if not _TOKEN_MIN <= len(token) <= _TOKEN_MAX:
        raise ValueError(f"token must be {_TOKEN_MIN}-{_TOKEN_MAX} characters")
    if not _TOKEN_RE.fullmatch(token):
        raise ValueError("token contains invalid characters")
    return token
