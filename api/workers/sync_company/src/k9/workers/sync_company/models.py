from typing import Any, Mapping

from k9.types.common import ResourceID
from pydantic import BaseModel, model_validator


class Resource(BaseModel, frozen=True):
    key: str
    id: ResourceID

    @model_validator(mode="before")
    @classmethod
    def parse_key(cls, data: Mapping[str, Any]):
        *_, id, _ = str(data["key"]).split("/")
        return {**data, "id": id}
