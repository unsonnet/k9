from __future__ import annotations

import os
from typing import Optional

from .ports import ImagesStoragePort, ProductsRepositoryPort, ReportsRepositoryPort, UsersRepositoryPort
from .repositories import (
    DynamoProductsRepository,
    DynamoReportsRepository,
    DynamoUsersRepository,
    MemoryProductsRepository,
    MemoryReportsRepository,
    MemoryUsersRepository,
    MemoryImagesStorage,
    S3ImagesStorage,
)


class Container:
    """Very small service container to select local vs cloud backends once.

    Current repositories auto-fallback to in-memory when env/credentials are missing.
    This container exposes a single point to switch implementations in the future if
    we add explicit memory implementations.
    """

    def __init__(self) -> None:
        # Choose backend once: 'memory' or 'cloud' (default: memory when under pytest)
        backend = os.getenv("K9_BACKEND")
        if not backend:
            # Default to in-memory for local/dev/tests unless explicitly set to 'cloud'
            backend = "memory"
        self._backend = backend
        self._users: Optional[UsersRepositoryPort] = None
        self._products: Optional[ProductsRepositoryPort] = None
        self._reports: Optional[ReportsRepositoryPort] = None
        self._images: Optional[ImagesStoragePort] = None

    def users_repo(self) -> UsersRepositoryPort:
        if self._users is None:
            self._users = MemoryUsersRepository() if self._backend == "memory" else DynamoUsersRepository()
        return self._users

    def products_repo(self) -> ProductsRepositoryPort:
        if self._products is None:
            self._products = MemoryProductsRepository() if self._backend == "memory" else DynamoProductsRepository()
        return self._products

    def reports_repo(self) -> ReportsRepositoryPort:
        if self._reports is None:
            self._reports = MemoryReportsRepository() if self._backend == "memory" else DynamoReportsRepository()
        return self._reports

    def images_store(self) -> ImagesStoragePort:
        if self._images is None:
            self._images = MemoryImagesStorage() if self._backend == "memory" else S3ImagesStorage()
        return self._images


_container = Container()


def container() -> Container:
    return _container
