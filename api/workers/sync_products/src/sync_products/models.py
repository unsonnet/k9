from typing import Any, Mapping

from pydantic import BaseModel, model_validator

__all__ = [
    "Sync",
]


class Sync:
    class Subresource(BaseModel, frozen=True):
        key: str
        id: str
        sid: str

        @model_validator(mode="before")
        @classmethod
        def parse_key(cls, data: Mapping[str, Any]):
            *_, id, _, sid, _ = str(data["key"]).split("/")
            return {**data, "id": id, "sid": sid}
