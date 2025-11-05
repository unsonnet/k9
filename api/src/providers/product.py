#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Final, NoReturn
from uuid import UUID, uuid4
from datetime import datetime, timezone

import numpy as np

from config import boto3_client, boto3_resource, settings

from models.common import CategoryMap
from models.product import ProductName, StoredProduct
from utils.aws import _for_dynamo, _from_dynamo
from utils.errors import (
    DomainError,
    DomainConflict,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)


# ──────────────────────────────────────────────────────────────────────────────
# Product Provider
# ──────────────────────────────────────────────────────────────────────────────
class ProductDBProvider(ABC):
    """Manage product data contracts for backends."""

    @abstractmethod
    def get_product(self, *, pid: UUID) -> StoredProduct:
        """Retrieve product by id."""
        ...

    @abstractmethod
    def post_product(
        self,
        *,
        name: ProductName,
        category: CategoryMap,
    ) -> StoredProduct:
        """Create product record."""
        ...

    @abstractmethod
    def put_product(self, *, product: StoredProduct) -> StoredProduct:
        """Replace product record."""
        ...

    @abstractmethod
    def delete_product(self, *, pid: UUID) -> None:
        """Delete product record."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopProductDBProvider(ProductDBProvider):
    """Manage product operations as a disabled provider."""

    _MSG: Final = "Failed to perform product operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def get_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def post_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def put_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def delete_product(self, *_, **__) -> None:
        self._raise()


# ──────────────────────────────────────────────────────────────────────────────
# DynamoDB Provider
# ──────────────────────────────────────────────────────────────────────────────
class DynamoProductDBProvider(ProductDBProvider):
    """Manage product data using AWS DynamoDB."""

    def __init__(self) -> None:
        cfg = settings()
        if not cfg.products_table:
            raise DomainInvariantViolation("Failed to initialize product provider.")

        self._table = boto3_resource("dynamodb").Table(cfg.products_table)
        self._client = boto3_client("dynamodb")

    # ─────────── Helpers ───────────
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_item(model: StoredProduct) -> dict[str, Any]:
        return _for_dynamo(model.model_dump(mode="python"))

    @staticmethod
    def _from_item(ddb_item: dict[str, Any]) -> StoredProduct:
        return StoredProduct.model_validate(_from_dynamo(ddb_item))

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        c = self._client.exceptions
        m: dict[type[Exception], type[DomainError]] = {
            c.ConditionalCheckFailedException: DomainConflict,
            c.ProvisionedThroughputExceededException: DomainRateLimited,
            c.ThrottlingException: DomainRateLimited,
            c.RequestLimitExceeded: DomainRateLimited,
            c.ResourceNotFoundException: DomainNotFound,
            c.TransactionConflictException: DomainConflict,
        }
        raise m.get(type(e), DomainInvariantViolation)(msg) from e

    # ─────────── Contract Methods ───────────
    def get_product(self, *, pid: UUID) -> StoredProduct:
        try:
            resp = self._table.get_item(Key={"id": str(pid)})
            item = resp.get("Item")
            if not item:
                raise DomainNotFound("Product not found.")
            return self._from_item(item)
        except Exception as e:
            self._handle_error(e, "Failed to fetch product.")

    def post_product(
        self, *, name: ProductName, category: CategoryMap
    ) -> StoredProduct:
        try:
            p = StoredProduct(
                id=uuid4(),
                name=name,
                category=category,
                formats=[],
                images=[],
                globalEmbedding=np.zeros((0,), dtype=np.float32),
                createdAt=self._now(),
            )
            self._table.put_item(
                Item=self._to_item(p),
                ConditionExpression="attribute_not_exists(id)",
            )
            return p
        except Exception as e:
            self._handle_error(e, "Failed to create product.")

    def put_product(self, *, product: StoredProduct) -> StoredProduct:
        try:
            self._table.put_item(
                Item=self._to_item(product),
                ConditionExpression="attribute_exists(id)",
            )
            resp = self._table.get_item(Key={"id": str(product.id)})
            item = resp.get("Item")
            if not item:
                raise DomainNotFound("Product not found.")
            return self._from_item(item)
        except Exception as e:
            self._handle_error(e, "Failed to update product.")

    def delete_product(self, *, pid: UUID) -> None:
        try:
            self._table.delete_item(
                Key={"id": str(pid)},
                ConditionExpression="attribute_exists(id)",
            )
        except Exception as e:
            self._handle_error(e, "Failed to delete product.")
