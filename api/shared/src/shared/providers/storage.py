from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import boto3
from types_boto3_s3.service_resource import Bucket

from ..config import GrantSpec
from ..errors import DomainForbidden, DomainNotFound, DomainUnknown
from . import BaseProvider, ExceptionMap, apimethod

__all__ = [
    "UploadURL",
    "StorageProvider",
]


@dataclass(frozen=True, slots=True)
class UploadURL:
    url: str
    fields: dict[str, str]


class StorageProvider(BaseProvider):
    _s3: Bucket

    def __init__(
        self,
        *,
        region: str,
        bucket: str,
    ) -> None:
        self._s3 = boto3.resource("s3", region_name=region).Bucket(bucket)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "s3:GetObject",
                "s3:PutObject",
            ),
            resources=("s3-bucket",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
        sx = self._s3.meta.client.exceptions
        return {
            DomainForbidden: [
                sx.AccessDenied,
            ],
            DomainNotFound: [
                sx.NoSuchBucket,
                sx.NoSuchKey,
            ],
        }

    # ──── Public Methods ────

    @apimethod
    def presign_post(
        self,
        key: str,
        *,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadURL:
        return self._upload_url(
            self._s3.meta.client.generate_presigned_post(
                Bucket=self._s3.name,
                Key=key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, max_bytes],
                ],
                ExpiresIn=max_seconds,
            )
        )

    # ──── Private Methods ────

    @staticmethod
    def _upload_url(response: Mapping[str, Any]) -> UploadURL:
        match response:
            case {"url": str(url), "fields": dict(fields)}:
                return UploadURL(
                    url=url,
                    fields={str(key): str(value) for key, value in fields.items()},
                )
        raise DomainUnknown(f"Unexpected s3 upload url: {response}")
