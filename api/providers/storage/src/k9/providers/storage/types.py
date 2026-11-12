from dataclasses import dataclass

from pydantic import HttpUrl
from types_boto3_s3.type_defs import GetObjectOutputTypeDef

__all__ = [
    "HttpUrl",
    "StorageObject",
    "Upload",
]


type StorageObject = GetObjectOutputTypeDef


@dataclass(frozen=True, slots=True)
class Upload:
    url: HttpUrl
    headers: dict[str, str]
