from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import boto3
from botocore.config import Config
from pydantic import HttpUrl
from shared.errors import DomainForbidden, DomainNotFound
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
    headers: dict[str, str]


class StorageProvider(BaseProvider):
    _s3: Bucket

    def __init__(
        self,
        *,
        region: str,
        bucket: str,
    ) -> None:
        self._s3 = boto3.resource(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            config=Config(s3={"addressing_style": "virtual"}),
        ).Bucket(bucket)

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
    def presign_put(
        self,
        key: str,
        *,
        content_type: str,
        content_length: int,
        max_seconds: int,
        metadata: Mapping[str, str] = {},
    ) -> UploadURL:
        url = self._s3.meta.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self._s3.name,
                "Key": key,
                "ContentType": content_type,
                "ContentLength": content_length,
                "IfNoneMatch": "*",
                "Metadata": dict(metadata),
            },
            ExpiresIn=max_seconds,
            HttpMethod="PUT",
        )
        return UploadURL(
            url=HttpUrl(url),
            headers={
                "Content-Type": content_type,
                "Content-Length": str(content_length),
                "If-None-Match": "*",
                **{f"x-amz-meta-{k}": v for k, v in metadata.items()},
            },
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
