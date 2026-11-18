from k9.types.base import ResourceModel
from pydantic import HttpUrl
from types_boto3_s3.type_defs import GetObjectOutputTypeDef

__all__ = [
    "HttpUrl",
    "StorageObject",
    "UploadForm",
]


type StorageObject = GetObjectOutputTypeDef


class UploadForm(ResourceModel, frozen=True):
    url: HttpUrl
    headers: dict[str, str]
