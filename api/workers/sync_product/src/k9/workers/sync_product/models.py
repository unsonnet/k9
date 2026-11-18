from typing import Any, Mapping

from k9.types.common import ResourceID, SubresourceID
from pydantic import BaseModel, model_validator


class Subresource(BaseModel, frozen=True):
    key: str
    id: ResourceID
    sid: SubresourceID

    @model_validator(mode="before")
    @classmethod
    def parse_key(cls, data: Mapping[str, Any]):
        *_, id, _, sid, _ = str(data["key"]).split("/")
        return {**data, "id": id, "sid": sid}
