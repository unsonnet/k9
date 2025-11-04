#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn
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
