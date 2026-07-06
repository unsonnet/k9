import re
from secrets import SystemRandom
from string import digits
from typing import Final

_RANDOM: Final = SystemRandom()


# ──── ID ──────────────────────────────────────────────────────────────────────────────


_ID_LENGTH: Final = 11
_ID_RE: Final = re.compile(r"^\d{3}-\d{3}-\d{3}$")


def generate_id() -> str:
    id = "".join(_RANDOM.choice(digits) for _ in range(9))
    id = id[:3] + "-" + id[3:6] + "-" + id[6:]
    return validate_id(id)


def validate_id(id: str) -> str:
    if len(id) != _ID_LENGTH:
        raise ValueError(f"id must be exactly {_ID_LENGTH} characters")
    if not _ID_RE.fullmatch(id):
        raise ValueError("id contains invalid characters")
    return id


# ──── SUB ID ──────────────────────────────────────────────────────────────────────────


_SID_LENGTH: Final = 4
_SID_RE: Final = re.compile(r"^\d{4}$")


def generate_sub_id() -> str:
    id = "".join(_RANDOM.choice(digits) for _ in range(4))
    return validate_sub_id(id)


def validate_sub_id(id: str) -> str:
    if len(id) != _SID_LENGTH:
        raise ValueError(f"sub id must be exactly {_SID_LENGTH} characters")
    if not _SID_RE.fullmatch(id):
        raise ValueError("sub id contains invalid characters")
    return id
