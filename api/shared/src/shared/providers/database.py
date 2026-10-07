from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Self, cast

import boto3
from boto3.dynamodb.conditions import Key
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb.type_defs import (
    TableAttributeValueTypeDef,
    TransactWriteItemTypeDef,
)

from ..errors import DomainInvariantViolation, DomainNotFound, DomainRateLimited
from ..helpers import now
from . import BaseProvider, ExceptionMap, GrantSpec, apimethod

__all__ = [
    "DatabaseTypes",
    "DatabaseProvider",
    "DatabaseBatchProvider",
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
        for (k, _), node in self.subitems.items():
            subitems.setdefault(f"${k}", []).append(node.serialize())
        return self.item | subitems


class DatabaseBatchProvider(AbstractContextManager, BaseProvider):
    _db: Table
    _txs: dict[tuple[str, str], TransactWriteItemTypeDef | None]

    def __init__(
        self,
        *,
        region: str,
        table: str,
    ) -> None:
        self._db = boto3.resource("dynamodb", region_name=region).Table(table)
        self._txs = {}

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "dynamodb:BatchWriteItem",
                "dynamodb:ConditionCheckItem",
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
    def __enter__(self) -> Self:
        self._txs.clear()
        return self

    @apimethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is not None:
            return None
        self._txs.pop(("", ""), None)
        txs = [tx or self._exists(*key) for key, tx in sorted(self._txs.items())]
        self._db.meta.client.transact_write_items(TransactItems=txs)
        return None

    @apimethod
    def check_item(
        self,
        *,
        type: str,
        id: str,
    ) -> None:
        if self._txs.get((type, id)):
            raise DomainInvariantViolation
        self._txs[type, id] = self._exists(type, id)
        return None

    @apimethod
    def create_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> None:
        if self._txs.get((type, id)):
            raise DomainInvariantViolation
        pk, sk = self._keys(type, id)
        self._txs[type, id] = {
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
        self._txs.setdefault(self._parent(type, id), None)
        return None

    @apimethod
    def query_item(
        self,
        *,
        type: str,
        id: str,
    ) -> Iterable[dict[str, DatabaseTypes]]:
        pk, sk = self._keys(type, id)
        expr = Key("pk").eq(pk)
        if sk != "META":
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

    @apimethod
    def update_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> None:
        if self._txs.get((type, id)):
            raise DomainInvariantViolation
        pk, sk = self._keys(type, id)
        attrs["updated_at"] = now().isoformat()
        names = {f"#n{i}": n for i, n in enumerate(attrs.keys())}
        values = {f":v{i}": v for i, v in enumerate(attrs.values())}
        updates = "SET " + ", ".join(f"{n} = {v}" for n, v in zip(names, values))
        self._txs[type, id] = {
            "Update": {
                "TableName": self._db.name,
                "Key": {"pk": pk, "sk": sk},
                "UpdateExpression": updates,
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": values,
                "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
            }
        }
        return None

    @apimethod
    def delete_item(
        self,
        *,
        type: str,
        id: str,
    ) -> None:
        for item in self.query_item(type=type, id=id):
            type, id = str(item["type"]), str(item["id"])
            if self._txs.get((type, id)):
                raise DomainInvariantViolation
            pk, sk = str(item["pk"]), str(item["sk"])
            self._txs[type, id] = {
                "Delete": {
                    "TableName": self._db.name,
                    "Key": {"pk": pk, "sk": sk},
                }
            }
        return None

    # ──── Private Methods ────

    def _exists(self, type: str, id: str) -> TransactWriteItemTypeDef:
        pk, sk = self._keys(type, id)
        return {
            "ConditionCheck": {
                "TableName": self._db.name,
                "Key": {"pk": pk, "sk": sk},
                "ConditionExpression": (
                    "attribute_exists(pk) AND attribute_exists(sk)"
                ),
            }
        }

    @staticmethod
    def _keys(type: str, id: str) -> tuple[str, str]:
        tags = [f"{t}#{i}" for t, i in zip(type.split("."), id.split("."))]
        return tags[0], ";".join(tags[1:]) or "META"

    @staticmethod
    def _parent(type: str, id: str) -> tuple[str, str]:
        return ".".join(type.split(".")[:-1]), ".".join(id.split(".")[1:])


class DatabaseProvider(BaseProvider):
    _db: DatabaseBatchProvider

    def __init__(
        self,
        *,
        region: str,
        table: str,
    ) -> None:
        self._db = DatabaseBatchProvider(region=region, table=table)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions

    # ──── Public Methods ────

    @apimethod
    def batch(self) -> DatabaseBatchProvider:
        return self._db

    @apimethod
    def create_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> None:
        with self.batch() as batch:
            batch.create_item(
                type=type,
                id=id,
                **attrs,
            )
        return None

    @apimethod
    def read_item(
        self,
        *,
        type: str,
        id: str,
    ) -> dict[str, DatabaseTypes]:
        root = Node()
        skip = type.count(".") + 1
        for item in self._db.query_item(type=type, id=id):
            node = root
            types, ids = cast(tuple[str, str], (item["type"], item["id"]))
            for kv in zip(types.split(".")[skip:], ids.split(".")[skip:]):
                node = node.subitems.setdefault(kv, Node())
            node.item = item
        return root.serialize()

    @apimethod
    def update_item(
        self,
        *,
        type: str,
        id: str,
        **attrs: DatabaseTypes,
    ) -> None:
        with self.batch() as batch:
            batch.update_item(
                type=type,
                id=id,
                **attrs,
            )
        return None

    @apimethod
    def delete_item(
        self,
        *,
        type: str,
        id: str,
    ) -> None:
        with self.batch() as batch:
            batch.delete_item(
                type=type,
                id=id,
            )
        return None
