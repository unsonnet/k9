import base64
import re
import unicodedata
from secrets import SystemRandom
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Final
from uuid import uuid4

from shared.errors import DomainInvariantViolation

_RANDOM: Final = SystemRandom()
_WHITESPACE_RE: Final = re.compile(r"\s+")
_TOKEN_RE: Final = re.compile(r"^[A-Za-z0-9-_=.]+$")

_ID_PREFIX: Final = "id:"

_NAME_PREFIX: Final = "name:"
_NAME_MIN_LENGTH: Final = 1
_NAME_MAX_LENGTH: Final = 2048

_PASSWORD_LENGTH: Final = 24
_PASSWORD_MIN_LENGTH: Final = 8
_PASSWORD_MAX_LENGTH: Final = 256
_PASSWORD_SPECIALS: Final = "!@#$%^&*()-_=+[]{}:,.?"
_PASSWORD_ALPHABET: Final = (
    ascii_lowercase + ascii_uppercase + digits + _PASSWORD_SPECIALS
)

_SESSION_MIN_LENGTH: Final = 20
_SESSION_MAX_LENGTH: Final = 2048

_TOKEN_MIN_LENGTH: Final = 1
_TOKEN_MAX_LENGTH: Final = 131072


# ──── ID ──────────────────────────────────────────────────────────────────────────────


def generate_id() -> str:
    return str(uuid4())


def encode_id(id: str) -> str:
    return f"{_ID_PREFIX}{id}"


def decode_id(xid: str) -> str:
    if not xid.startswith(_ID_PREFIX):
        raise DomainInvariantViolation(f"Unexpected Cognito user id format: {xid}")
    return xid.removeprefix(_ID_PREFIX)


# ──── Name ────────────────────────────────────────────────────────────────────────────


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return _WHITESPACE_RE.sub(" ", name.strip()).casefold()


def encode_name(name: str) -> str:
    return f"{_NAME_PREFIX}{base64.b64encode(name.encode()).decode('ascii')}"


def decode_name(xname: str) -> str:
    if not xname.startswith(_NAME_PREFIX):
        raise DomainInvariantViolation(f"Unexpected Cognito username format: {xname}")
    return base64.b64decode(xname.removeprefix(_NAME_PREFIX)).decode()


def validate_name(name: str) -> str:
    name = normalize_name(name)
    if not _NAME_MIN_LENGTH <= len(name) <= _NAME_MAX_LENGTH:
        raise ValueError(
            f"name must be {_NAME_MIN_LENGTH}-{_NAME_MAX_LENGTH} characters"
        )
    if len(encode_name(name)) > _NAME_MAX_LENGTH:
        raise ValueError(f"encoded name cannot exceed {_NAME_MAX_LENGTH} characters")

    return name


# ──── Password ────────────────────────────────────────────────────────────────────────


def generate_password(length: int = _PASSWORD_LENGTH) -> str:
    chars = [
        _RANDOM.choice(ascii_lowercase),
        _RANDOM.choice(ascii_uppercase),
        _RANDOM.choice(digits),
        _RANDOM.choice(_PASSWORD_SPECIALS),
    ]
    chars += [_RANDOM.choice(_PASSWORD_ALPHABET) for _ in range(length - len(chars))]
    _RANDOM.shuffle(chars)
    return validate_password("".join(chars))


def validate_password(password: str) -> str:
    if not _PASSWORD_MIN_LENGTH <= len(password) <= _PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"password must be {_PASSWORD_MIN_LENGTH}-{_PASSWORD_MAX_LENGTH} characters"
        )
    if any(char.isspace() for char in password):
        raise ValueError("password cannot contain whitespace")
    if not any(char.isupper() for char in password):
        raise ValueError("password must contain an uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("password must contain a lowercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("password must contain a number")
    if not any(char in _PASSWORD_SPECIALS for char in password):
        raise ValueError("password must contain a symbol")

    return password


# ──── Session ─────────────────────────────────────────────────────────────────────────


def validate_session(session: str) -> str:
    if not _SESSION_MIN_LENGTH <= len(session) <= _SESSION_MAX_LENGTH:
        raise ValueError(
            f"session must be {_SESSION_MIN_LENGTH}-{_SESSION_MAX_LENGTH} characters"
        )
    return session


# ──── Token ───────────────────────────────────────────────────────────────────────────


def validate_token(token: str) -> str:
    if not _TOKEN_MIN_LENGTH <= len(token) <= _TOKEN_MAX_LENGTH:
        raise ValueError(
            f"token must be {_TOKEN_MIN_LENGTH}-{_TOKEN_MAX_LENGTH} characters"
        )

    if not _TOKEN_RE.fullmatch(token):
        raise ValueError("token contains invalid characters")

    return token
