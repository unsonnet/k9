from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from itertools import batched
from typing import Self

import boto3
from boto3.dynamodb.conditions import Key
from shared.errors import DomainInvariantViolation, DomainNotFound, DomainRateLimited
from shared.helpers import now
from shared.providers.base import BaseProvider, ExceptionMap, GrantSpec, apimethod
from types_boto3_dynamodb.service_resource import Table
from types_boto3_dynamodb.type_defs import (
    TableAttributeValueTypeDef,
    TransactWriteItemTypeDef,
)

__all__ = [
    "DatabaseTypes",
    "DatabaseBatchProvider",
]


type DatabaseTypes = TableAttributeValueTypeDef


class DatabaseBatchProvider(AbstractContextManager, BaseProvider):
    _db: Table
    _txs: dict[str, TransactWriteItemTypeDef | None]

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
        self._txs.pop("", None)
        txs = [tx or self._exists(key) for key, tx in sorted(self._txs.items())]
        self._db.meta.client.transact_write_items(TransactItems=txs)
        return None

    @apimethod
    def check_item(self, key: str) -> None:
        if self._txs.get(key):
            raise DomainInvariantViolation
        self._txs[key] = self._exists(key)
        return None

    @apimethod
    def create_item(self, key: str, **attrs: DatabaseTypes) -> None:
        if self._txs.get(key):
            raise DomainInvariantViolation
        pk, sk = self._index(key)
        self._txs[key] = {
            "Put": {
                "TableName": self._db.name,
                "Item": dict(
                    pk=pk,
                    sk=sk,
                    key=self._expand(key),
                    **attrs,
                    created_at=now().isoformat(),
                    updated_at=None,
                ),
                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
            }
        }
        self._txs.setdefault(self._parent(key), None)
        return None

    @apimethod
    def query_item(self, key: str) -> Iterable[dict[str, DatabaseTypes]]:
        pk, sk = self._index(key)
        expr = Key("pk").eq(pk) & Key("sk").begins_with(sk)
        resp = self._db.query(KeyConditionExpression=expr, ConsistentRead=True)
        yield from resp["Items"]
        while cursor := resp.get("LastEvaluatedKey"):
            resp = self._db.query(
                KeyConditionExpression=expr,
                ConsistentRead=True,
                ExclusiveStartKey=cursor,
            )
            yield from resp["Items"]

    @apimethod
    def update_item(self, key: str, **attrs: DatabaseTypes) -> None:
        if self._txs.get(key):
            raise DomainInvariantViolation
        pk, sk = self._index(key)
        attrs["updated_at"] = now().isoformat()
        names = {f"#n{i}": n for i, n in enumerate(attrs.keys())}
        values = {f":v{i}": v for i, v in enumerate(attrs.values())}
        updates = "SET " + ", ".join(f"{n} = {v}" for n, v in zip(names, values))
        self._txs[key] = {
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
    def delete_item(self, key: str) -> None:
        for item in self.query_item(key):
            subkey = str(item["key"]["key"])  # type: ignore
            if self._txs.get(subkey):
                raise DomainInvariantViolation
            self._txs[subkey] = {
                "Delete": {
                    "TableName": self._db.name,
                    "Key": {"pk": item["pk"], "sk": item["sk"]},
                }
            }
        return None

    # ──── Private Methods ────

    def _exists(self, key: str) -> TransactWriteItemTypeDef:
        pk, sk = self._index(key)
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
    def _index(key: str) -> tuple[str, str]:
        path = [f"{t}#{i}" for t, i in batched(key.split("/"), 2)]
        return path[0], ";".join(path)

    @staticmethod
    def _expand(key: str) -> dict[str, str]:
        path = key.split("/")
        return {"key": key, "type": "/".join(path[::2]), "id": "/".join(path[1::2])}

    @staticmethod
    def _parent(key: str) -> str:
        return "/".join(key.split("/")[:-2])
