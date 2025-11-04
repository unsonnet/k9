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
from models.product import (
    ProductName,
    StoredProduct,
    ImageMask,
    HomographyMatrix,
    LocalEmbeddings,
    GlobalEmbedding,
    AnyUrl,
)
from utils.errors import (
    DomainError,
    DomainForbidden,
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
        # json-mode yields str(UUID), ISO datetimes, str(AnyUrl), and lists for np arrays
        return model.model_dump(mode="json")

    @staticmethod
    def _from_item(ddb_item: dict[str, Any]) -> StoredProduct:
        # validators reconstruct numpy arrays and enforce shapes/dtypes
        return StoredProduct.model_validate(ddb_item)

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        c = self._client.exceptions
        m: dict[type[Exception], type[DomainError]] = {
            c.ConditionalCheckFailedException: DomainConflict,
            c.ProvisionedThroughputExceededException: DomainRateLimited,
            c.ThrottlingException: DomainRateLimited,
            c.RequestLimitExceeded: DomainRateLimited,
            c.ResourceNotFoundException: DomainNotFound,
            c.TransactionConflictException: DomainConflict,
            c.ValidationException: DomainInvariantViolation,
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


# ──────────────────────────────────────────────────────────────────────────────
# Image Provider
# ──────────────────────────────────────────────────────────────────────────────
class ImageDBProvider(ABC):
    """Manage image storage, transformation, metadata, and embeddings."""

    @abstractmethod
    def post_image(
        self,
        *,
        pid: UUID,
        image: bytes,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        """
        Store original image, apply optional mask/homography to produce transformed
        variant, and compute embeddings.

        Returns:
            (iid, local_vectors, global_vector)
        """
        ...

    @abstractmethod
    def put_image(
        self,
        *,
        pid: UUID,
        iid: UUID,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        """
        Update image transformation metadata (mask/homography) and recompute
        embeddings for the image and product.

        Returns:
            (local_vectors, global_vector)
        """
        ...

    @abstractmethod
    def get_url(self, *, pid: UUID, iid: UUID, original: bool) -> AnyUrl:
        """Retrieve a URL for the original or transformed image."""
        ...

    @abstractmethod
    def delete_image(self, *, pid: UUID, iid: UUID) -> None:
        """Delete image and any derived artifacts."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopImageDBProvider(ImageDBProvider):
    """Manage image operations as a disabled provider."""

    _MSG: Final = "Failed to perform image operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def post_image(self, *_, **__) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        self._raise()

    def put_image(self, *_, **__) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        self._raise()

    def get_url(self, *_, **__) -> AnyUrl:
        self._raise()

    def delete_image(self, *_, **__) -> None:
        self._raise()


# ──────────────────────────────────────────────────────────────────────────────
# S3 Provider
# ──────────────────────────────────────────────────────────────────────────────
class S3ImageDBProvider(ImageDBProvider):
    """Manage product images and transformed variants using AWS S3."""

    def __init__(self) -> None:
        cfg = settings()
        if not cfg.images_bucket:
            raise DomainInvariantViolation("Failed to initialize image provider.")

        self.bucket: str = cfg.images_bucket
        self._s3 = boto3_client("s3")

    # ─────────── Internal helpers ───────────
    @staticmethod
    def _local_vectors_empty() -> LocalEmbeddings:
        return np.zeros((0, 0), dtype=np.float32)

    @staticmethod
    def _global_vector_empty() -> GlobalEmbedding:
        return np.zeros((0,), dtype=np.float32)

    @staticmethod
    def _key(pid: UUID, iid: UUID, *, original: bool) -> str:
        if original:
            return f"products/{pid}/{iid}/original"
        return f"products/{pid}/{iid}/transformed"

    def _handle_s3_error(self, e: Exception, msg: str) -> NoReturn:
        from botocore.exceptions import ClientError, BotoCoreError

        if isinstance(e, ClientError):
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                raise DomainNotFound(msg) from e
            if code in ("Throttling", "ThrottlingException"):
                raise DomainRateLimited(msg) from e
            if code in ("AccessDenied", "Forbidden"):
                raise DomainForbidden(msg) from e

        elif isinstance(e, BotoCoreError):
            raise DomainRateLimited(msg) from e

        raise DomainInvariantViolation(msg) from e

    # ─────────── Contract Methods ───────────
    def post_image(
        self,
        *,
        pid: UUID,
        image: bytes,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        iid = uuid4()
        try:
            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=True),
                Body=image,
                ContentType="image/jpeg",
            )
            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=False),
                Body=image,
                ContentType="image/jpeg",
            )

            return (
                iid,
                self._local_vectors_empty(),
                self._global_vector_empty(),
            )

        except Exception as e:
            self._handle_s3_error(e, "Failed to store product image.")

    def put_image(
        self,
        *,
        pid: UUID,
        iid: UUID,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        try:
            obj = self._s3.get_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=True),
            )
            original_bytes = obj["Body"].read()

            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=False),
                Body=original_bytes,
                ContentType="image/jpeg",
            )

            return (
                self._local_vectors_empty(),
                self._global_vector_empty(),
            )

        except Exception as e:
            self._handle_s3_error(e, "Failed to update product image.")

    def get_url(self, *, pid: UUID, iid: UUID, original: bool) -> AnyUrl:
        key = self._key(pid, iid, original=original)
        try:
            url = self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=3600,
            )
            return AnyUrl(url)
        except Exception as e:
            self._handle_s3_error(e, "Failed to generate image URL.")

    def delete_image(self, *, pid: UUID, iid: UUID) -> None:
        try:
            self._s3.delete_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=True),
            )
            self._s3.delete_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, original=False),
            )
        except Exception as e:
            self._handle_s3_error(e, "Failed to delete product image.")
