#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn, Sequence
from uuid import UUID, uuid4

import numpy as np

from config import boto3_client, settings

from models.product import (
    ImageMask,
    HomographyMatrix,
    LocalEmbeddings,
    GlobalEmbedding,
    AnyUrl,
)
from utils.errors import (
    DomainError,
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)


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
    def get_url(self, *, pid: UUID, iid: UUID, transformed: bool) -> AnyUrl:
        """Retrieve a URL for the original or transformed image."""
        ...

    @abstractmethod
    def delete_images(
        self, *, pid: UUID, iids: Sequence[UUID]
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
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

    def delete_images(self, *_, **__) -> tuple[LocalEmbeddings, GlobalEmbedding]:
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

    # ─────────── Helpers ───────────
    @staticmethod
    def _local_vectors_empty() -> LocalEmbeddings:
        return np.zeros((1, 1), dtype=np.float32)

    @staticmethod
    def _global_vector_empty() -> GlobalEmbedding:
        return np.zeros((1,), dtype=np.float32)

    @staticmethod
    def _key(pid: UUID, iid: UUID, *, transformed: bool) -> str:
        return (
            f"products/{pid}/{iid}/transformed"
            if transformed
            else f"products/{pid}/{iid}/original"
        )

    def _handle_error(self, e: Exception, msg: str) -> NoReturn:
        c = self._s3.exceptions
        mapping: dict[type[Exception], type[DomainError]] = {
            c.NoSuchKey: DomainNotFound,
            c.NoSuchBucket: DomainNotFound,
            c.AccessDenied: DomainForbidden,
            c.InvalidObjectState: DomainForbidden,
            c.Throttling: DomainRateLimited,
            c.SlowDown: DomainRateLimited,
            c.RequestTimeout: DomainRateLimited,
        }
        raise mapping.get(type(e), DomainInvariantViolation)(msg) from e

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
            # Store original and transformed (placeholder) same as before
            for transformed in (False, True):
                self._s3.put_object(
                    Bucket=self.bucket,
                    Key=self._key(pid, iid, transformed=transformed),
                    Body=image,
                    ContentType="image/jpeg",
                )
            return (iid, self._local_vectors_empty(), self._global_vector_empty())
        except Exception as e:
            self._handle_error(e, "Failed to store product image.")

    def put_image(
        self,
        *,
        pid: UUID,
        iid: UUID,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        try:
            # Pull transformed -> re-store original
            obj = self._s3.get_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, transformed=True),
            )
            original_bytes = obj["Body"].read()

            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, transformed=False),
                Body=original_bytes,
                ContentType="image/jpeg",
            )

            return (self._local_vectors_empty(), self._global_vector_empty())
        except Exception as e:
            self._handle_error(e, "Failed to update product image.")

    def get_url(self, *, pid: UUID, iid: UUID, transformed: bool) -> AnyUrl:
        key = self._key(pid, iid, transformed=transformed)
        try:
            # Exactly one call: HEAD to enforce 404 correctness.
            self._s3.head_object(Bucket=self.bucket, Key=key)

            url = self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=3600,
            )
            return AnyUrl(url)
        except Exception as e:
            self._handle_error(e, "Failed to generate image URL.")

    def delete_images(
        self, *, pid: UUID, iids: Sequence[UUID]
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        try:
            objects = [
                {"Key": self._key(pid, iid, transformed=t)}
                for iid in iids
                for t in (False, True)
            ]
            if objects:
                self._s3.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": objects, "Quiet": True},
                )
            return (self._local_vectors_empty(), self._global_vector_empty())
        except Exception as e:
            self._handle_error(e, "Failed to delete product image.")
