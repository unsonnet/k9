#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn, Sequence
from uuid import UUID

from models.domain.product import (
    ImageMask,
    HomographyMatrix,
    LocalEmbeddings,
    GlobalEmbedding,
)
from pydantic import AnyUrl
from utils.errors import DomainInvariantViolation


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
        reset: bool,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        """Update image transformation metadata and recompute embeddings."""
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
class NoopImageDBProvider(ImageDBProvider):
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
