from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Protocol


class UsersRepositoryPort(Protocol):
    def get(self, uid: str) -> Dict[str, Any]:
        ...

    def list(self, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        ...

    def put(self, item: Dict[str, Any]) -> None:
        ...

    def delete(self, uid: str) -> None:
        ...

    def get_by_cognito_sub(self, sub: str) -> Dict[str, Any]:
        ...


class ProductsRepositoryPort(Protocol):
    def get(self, pid: str) -> Dict[str, Any]:
        ...

    def put(self, item: Dict[str, Any]) -> None:
        ...

    def delete(self, pid: str) -> None:
        ...


class ReportsRepositoryPort(Protocol):
    def get(self, rid: str) -> Dict[str, Any]:
        ...

    def list_by_author(self, author: str, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        ...

    def put(self, item: Dict[str, Any]) -> None:
        ...

    def delete(self, rid: str) -> None:
        ...


class ImagesStoragePort(Protocol):
    def put_image(self, key: str, data: bytes, content_type: str = "image/png") -> None:
        ...

    def presign(self, key: str, expires: int = 3600) -> str:
        ...
