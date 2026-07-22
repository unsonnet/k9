from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Sequence, cast

import boto3
from boto3.dynamodb.conditions import Key
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb.type_defs import (
    TableAttributeValueTypeDef,
    TransactWriteItemTypeDef,
)

from ..config import GrantSpec
from ..errors import DomainNotFound, DomainRateLimited
from ..helpers import now
from . import BaseProvider, ExceptionMap, apimethod

__all__ = [
    "DatabaseTypes",
    "DatabaseProvider",
]


type DatabaseTypes = TableAttributeValueTypeDef


@dataclass
class _Node:
    item: dict[str, DatabaseTypes] = field(default_factory=dict)
    subitems: dict[tuple[str, str], "_Node"] = field(default_factory=dict)

    def serialize(self) -> dict[str, DatabaseTypes]:
        subitems: dict[str, list[dict[str, DatabaseTypes]]] = {}
        for (k, _), node in self.subitems.items():
            subitems.setdefault(f".{k}", []).append(node.serialize())
        return self.item | subitems


class DatabaseProvider(BaseProvider):
    _db: Table

    def __init__(
        self,
        *,
        region: str,
        table: str,
    ) -> None:
        self._db = boto3.resource("dynamodb", region_name=region).Table(table)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "dynamodb:BatchWriteItem",
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:TransactWriteItems",
                "dynamodb:UpdateItem",
            ),
            resources=("dynamodb-table",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
        dx = self._db.meta.client.exceptions
        return {
            DomainRateLimited: [
                dx.ProvisionedThroughputExceededException,
                dx.RequestLimitExceeded,
                dx.ThrottlingException,
            ],
            DomainNotFound: [
                dx.ConditionalCheckFailedException,
                dx.ResourceNotFoundException,
            ],
        }

    # ──── Public Methods ────

    @apimethod
    def create_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> dict[str, DatabaseTypes]:
        pk, sk = self._keys(type=type, id=id)
        tx: Sequence[TransactWriteItemTypeDef] = [
            {
                "Put": {
                    "TableName": self._db.name,
                    "Item": dict(
                        type=type,
                        id=id,
                        pk=pk,
                        sk=sk,
                        **attrs,
                        created_at=now().isoformat(),
                        updated_at=None,
                    ),
                    "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                }
            }
        ]
        if sk != "META":
            pk, sk = self._keys(type=type, id=id, parent=True)
            tx.append(
                {
                    "ConditionCheck": {
                        "TableName": self._db.name,
                        "Key": {"pk": pk, "sk": sk},
                        "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
                    }
                }
            )
        self._db.meta.client.transact_write_items(TransactItems=tx)
        return self.read_item(type=type, id=id)

    @apimethod
    def read_item(
        self,
        *,
        type: str,
        id: str,
        recurse: bool = True,
    ) -> dict[str, DatabaseTypes]:
        return self._hydrate(
            self._query(type=type, id=id, recurse=recurse),
            type=type,
        )

    @apimethod
    def update_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> dict[str, DatabaseTypes]:
        pk, sk = self._keys(type=type, id=id)
        attrs["updated_at"] = now().isoformat()
        names = {f"#n{i}": k for i, k in enumerate(attrs.keys())}
        values = {f":v{i}": v for i, v in enumerate(attrs.values())}
        updates = "SET " + ", ".join(f"{k} = {v}" for k, v in zip(names, values))
        self._db.update_item(
            Key={"pk": pk, "sk": sk},
            UpdateExpression=updates,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )
        return self.read_item(type=type, id=id)

    @apimethod
    def delete_item(
        self,
        *,
        type: str,
        id: str,
        recurse: bool = True,
    ) -> None:
        with self._db.batch_writer() as batch:
            for item in self._query(type=type, id=id, recurse=recurse):
                batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        return None

    # ──── Private Methods ────

    @staticmethod
    def _keys(*, type: str, id: str, parent: bool = False) -> tuple[str, str]:
        end = type.count(".") + 1 - parent
        tags = [f"{t}#{i}" for t, i in zip(type.split("."), id.split("."))][:end]
        return tags[0], ";".join(tags[1:]) or "META"

    def _query(
        self,
        *,
        type: str,
        id: str,
        recurse: bool,
    ) -> Iterable[dict[str, DatabaseTypes]]:
        pk, sk = self._keys(type=type, id=id)
        expr = Key("pk").eq(pk)
        if not recurse:
            expr &= Key("sk").eq(sk)
        elif sk != "META":
            expr &= Key("sk").begins_with(sk)
        response = self._db.query(KeyConditionExpression=expr, ConsistentRead=True)
        yield from response["Items"]
        while cursor := response.get("LastEvaluatedKey"):
            response = self._db.query(
                KeyConditionExpression=expr,
                ConsistentRead=True,
                ExclusiveStartKey=cursor,
            )
            yield from response["Items"]

    @staticmethod
    def _hydrate(
        items: Iterable[dict[str, DatabaseTypes]],
        /,
        type: str,
    ) -> dict[str, DatabaseTypes]:
        root = _Node()
        skip = type.count(".") + 1
        for item in items:
            node = root
            types, ids = cast(tuple[str, str], (item["type"], item["id"]))
            for kv in zip(types.split(".")[skip:], ids.split(".")[skip:]):
                node = node.subitems.setdefault(kv, _Node())
            node.item = item
        return root.serialize()
