import base64
from typing import Final

from shared.errors import DomainInvariantViolation

_COGNITO_ID_PREFIX: Final = "id:"
_COGNITO_NAME_PREFIX: Final = "name:"


def encode_id(id: str) -> str:
    return f"{_COGNITO_ID_PREFIX}{id}"


def decode_id(xid: str) -> str:
    if not xid.startswith(_COGNITO_ID_PREFIX):
        raise DomainInvariantViolation(f"Unexpected Cognito user id format: {xid}")
    return xid.removeprefix(_COGNITO_ID_PREFIX)


def encode_name(name: str) -> str:
    return f"{_COGNITO_NAME_PREFIX}{base64.b64encode(name.encode()).decode('ascii')}"


def decode_name(xname: str) -> str:
    if not xname.startswith(_COGNITO_NAME_PREFIX):
        raise DomainInvariantViolation(f"Unexpected Cognito username format: {xname}")
    return base64.b64decode(xname.removeprefix(_COGNITO_NAME_PREFIX)).decode()
