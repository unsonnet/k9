#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn
from uuid import UUID

from models.shared.types import CategoryMap
from models.shared.values import Name
from models.domain.product import ProductEntity
from utils.errors import DomainInvariantViolation


# ──────────────────────────────────────────────────────────────────────────────
# Product Provider
# ──────────────────────────────────────────────────────────────────────────────
class ProductDBProvider(ABC):
    """Manage product data contracts for backends."""

    @abstractmethod
    def get_product(self, *, pid: UUID) -> ProductEntity:
        """Retrieve product by id."""
        ...

    @abstractmethod
    def post_product(
        self,
        *,
        name: Name,
        category: CategoryMap,
    ) -> ProductEntity:
        """Create product record."""
        ...

    @abstractmethod
    def put_product(self, *, product: ProductEntity) -> ProductEntity:
        """Replace product record."""
        ...

    @abstractmethod
    def delete_product(self, *, pid: UUID) -> None:
        """Delete product record."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class NoopProductDBProvider(ProductDBProvider):
    """Manage product operations as a disabled provider."""

    _MSG: Final = "Failed to perform product operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def get_product(self, *_, **__) -> ProductEntity:
        self._raise()

    def post_product(self, *_, **__) -> ProductEntity:
        self._raise()

    def put_product(self, *_, **__) -> ProductEntity:
        self._raise()

    def delete_product(self, *_, **__) -> None:
        self._raise()
