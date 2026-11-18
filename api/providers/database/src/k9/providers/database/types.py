from __future__ import annotations

from dataclasses import dataclass, field

from k9.types.errors import DomainNotFound
from types_boto3_dynamodb.type_defs import TableAttributeValueTypeDef

__all__ = [
    "DatabaseTypes",
    "Node",
]


type DatabaseTypes = TableAttributeValueTypeDef


@dataclass
class Node:
    item: dict[str, DatabaseTypes] = field(default_factory=dict)
    subitems: dict[tuple[str, str], Node] = field(default_factory=dict)

    def serialize(self) -> dict[str, DatabaseTypes]:
        if not self.item:
            raise DomainNotFound
        subitems: dict[str, list[dict[str, DatabaseTypes]]] = {}
        for (t, _), node in self.subitems.items():
            subitems.setdefault(f"${t}", []).append(node.serialize())
        return self.item | subitems
