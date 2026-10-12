from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import boto3
from pydantic import HttpUrl
from shared.errors import DomainForbidden, DomainNotFound, DomainUnknown
from shared.providers.base import BaseProvider, ExceptionMap, GrantSpec, apimethod
from types_boto3_s3.service_resource import Bucket
from types_boto3_s3.type_defs import GetObjectOutputTypeDef

__all__ = [
    "UploadURL",
    "StorageProvider",
    "StorageObject",
]


type StorageObject = GetObjectOutputTypeDef


@dataclass(frozen=True, slots=True)
class UploadURL:
    url: HttpUrl
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
                "s3:DeleteObject",
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
        metadata: Mapping[str, str] = {},
    ) -> UploadURL:
        meta = {f"x-amz-meta-{k}": v for k, v in metadata.items()}
        return self._upload_url(
            self._s3.meta.client.generate_presigned_post(
                Bucket=self._s3.name,
                Key=key,
                Fields={"Content-Type": content_type, **meta},
                Conditions=[
                    {"Content-Type": content_type},
                    *({k: v} for k, v in meta.items()),
                    ["content-length-range", 1, max_bytes],
                ],
                ExpiresIn=max_seconds,
            )
        )

    @apimethod
    def get_url(
        self,
        key: str,
    ) -> HttpUrl:
        bucket, region = self._s3.name, self._s3.meta.client.meta.region_name
        return HttpUrl(f"https://{bucket}.s3.{region}.amazonaws.com/{key}")

    @apimethod
    def read(self, key: str) -> StorageObject:
        return self._s3.Object(key).get()

    @apimethod
    def write(self, key: str, data: bytes, *, content_type: str) -> None:
        self._s3.put_object(Key=key, Body=data, ContentType=content_type)

    @apimethod
    def delete(self, key: str) -> None:
        self._s3.Object(key).delete()

    # ──── Private Methods ────

    @staticmethod
    def _upload_url(response: Mapping[str, Any]) -> UploadURL:
        match response:
            case {"url": str(url), "fields": dict(fields)}:
                return UploadURL(
                    url=HttpUrl(url),
                    fields={str(key): str(value) for key, value in fields.items()},
                )
        raise DomainUnknown(f"Unexpected s3 upload url: {response}")
