from enum import StrEnum
from typing import Mapping

from shared.abc import DataModel


class Tokens(DataModel, frozen=True):
    access_token: str
    expires_in: int
    refresh_token: str
    id_token: str


class Challenge(DataModel, frozen=True):
    class Key(StrEnum):
        NEW_PASSWORD = "NEW_PASSWORD"
        NEW_MFA = "NEW_MFA"
        MFA = "MFA"

    session: str
    challenge: Key
    parameters: Mapping[str, str]
