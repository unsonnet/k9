import re
import unicodedata
from secrets import SystemRandom
from string import ascii_lowercase, ascii_uppercase, digits
from typing import Final

_RANDOM: Final = SystemRandom()


# ──── ID ──────────────────────────────────────────────────────────────────────────────


_ID_LENGTH: Final = 6
_ID_RE: Final = re.compile(r"^[a-z]{3}\d{3}$")


def generate_id() -> str:
    id = "".join(_RANDOM.choice(ascii_lowercase) for _ in range(3))
    id += "".join(_RANDOM.choice(digits) for _ in range(3))
    return validate_id(id)


def validate_id(id: str) -> str:
    if len(id) != _ID_LENGTH:
        raise ValueError(f"id must be exactly {_ID_LENGTH} characters")
    if not _ID_RE.fullmatch(id):
        raise ValueError("id contains invalid characters")
    return id


# ──── Name ────────────────────────────────────────────────────────────────────────────


_NAME_MIN: Final = 1
_NAME_MAX: Final = 1024


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return re.sub(r"\s+", " ", name.strip()).casefold()


def validate_name(name: str) -> str:
    name = normalize_name(name)
    if not _NAME_MIN <= len(name) <= _NAME_MAX:
        raise ValueError(f"name must be {_NAME_MIN}-{_NAME_MAX} characters")
    return name


# ──── Password ────────────────────────────────────────────────────────────────────────


_PASSWORD_MIN: Final = 8
_PASSWORD_MAX: Final = 256
_PASSWORD_SPECIALS: Final = "!@#$%^&*()-_=+[]{}:,.?"
_PASSWORD_ALPHABET: Final = (
    ascii_lowercase + ascii_uppercase + digits + _PASSWORD_SPECIALS
)


def generate_password(length: int = _PASSWORD_MIN) -> str:
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
    if not _PASSWORD_MIN <= len(password) <= _PASSWORD_MAX:
        raise ValueError(f"password must be {_PASSWORD_MIN}-{_PASSWORD_MAX} characters")
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
