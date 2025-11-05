#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from io import BytesIO
from typing import NoReturn, Sequence
from uuid import UUID, uuid4

import numpy as np
from PIL import Image

from config import boto3_client, settings

from models.domain.product import (
    ImageMask,
    HomographyMatrix,
    LocalEmbeddings,
    GlobalEmbedding,
)
from pydantic import AnyUrl
from utils.errors import (
    DomainError,
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)

from .base import ImageDBProvider


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

    @staticmethod
    def _infer_mime(image_bytes: bytes) -> str:
        try:
            with Image.open(BytesIO(image_bytes)) as im:
                fmt = (im.format or "").upper()
            mapping = {
                "JPEG": "image/jpeg",
                "JPG": "image/jpeg",
                "PNG": "image/png",
                "WEBP": "image/webp",
                "GIF": "image/gif",
                "TIFF": "image/tiff",
                "BMP": "image/bmp",
            }
            return mapping.get(fmt, "application/octet-stream")
        except Exception:
            return "application/octet-stream"

    @staticmethod
    def _apply_mask_as_alpha(base_bytes: bytes, mask: ImageMask | None) -> bytes:
        """
        Return a PNG bytes where the alpha channel is:
          - 255 everywhere if mask is None
          - 255 for True, 0 for False if mask provided
        Homography is intentionally ignored for now.
        """
        try:
            with Image.open(BytesIO(base_bytes)) as im:
                im = im.convert("RGBA")
                w, h = im.size

                if mask is None:
                    alpha = Image.new("L", (w, h), 255)
                else:
                    # Validate mask shape (H, W)
                    if mask.ndim != 2:
                        raise DomainInvariantViolation("Mask must be 2D (H, W).")
                    mh, mw = mask.shape
                    if (mw, mh) != (w, h):
                        raise DomainInvariantViolation(
                            f"Mask shape {(mh, mw)} does not match image size {(h, w)}."
                        )
                    alpha_arr = mask.astype(np.uint8) * 255
                    alpha = Image.fromarray(alpha_arr, mode="L")

                r, g, b, _ = im.split()
                out = Image.merge("RGBA", (r, g, b, alpha))

                buf = BytesIO()
                out.save(buf, format="PNG")
                return buf.getvalue()
        except DomainInvariantViolation:
            raise
        except Exception as e:
            raise DomainInvariantViolation("Failed to transform image.") from e

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
        homography: HomographyMatrix | None,  # ignored for now
    ) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        iid = uuid4()
        try:
            # 1) Store ORIGINAL exactly as provided.
            orig_ct = self._infer_mime(image)
            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, transformed=False),
                Body=image,
                ContentType=orig_ct,
            )

            # 2) Store TRANSFORMED as PNG with mask as alpha (or fully opaque).
            transformed_png = self._apply_mask_as_alpha(image, mask)
            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, transformed=True),
                Body=transformed_png,
                ContentType="image/png",
            )

            return (iid, self._local_vectors_empty(), self._global_vector_empty())
        except Exception as e:
            self._handle_error(e, "Failed to store product image.")

    def put_image(
        self,
        *,
        pid: UUID,
        iid: UUID,
        reset: bool,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,  # ignored for now
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        """
        Replace the transformed image.
        - If reset=True: use ORIGINAL as the base, then apply mask -> store TRANSFORMED (PNG).
        - If reset=False: use current TRANSFORMED as the base, then apply mask -> store TRANSFORMED (PNG).
        """
        try:
            base_key = self._key(pid, iid, transformed=not reset)
            obj = self._s3.get_object(Bucket=self.bucket, Key=base_key)
            base_bytes = obj["Body"].read()

            new_png = self._apply_mask_as_alpha(base_bytes, mask)

            self._s3.put_object(
                Bucket=self.bucket,
                Key=self._key(pid, iid, transformed=True),
                Body=new_png,
                ContentType="image/png",
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
