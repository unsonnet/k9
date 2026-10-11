from enum import StrEnum
from typing import Annotated, TypeVar

from aws_lambda_powertools.event_handler.openapi.params import Body as HTTPBody
from aws_lambda_powertools.event_handler.openapi.params import Path as HTTPPath
from aws_lambda_powertools.event_handler.openapi.params import Query as HTTPQuery

__all__ = [
    "Payload",
    "Body",
    "Path",
    "Query",
    "ImageFormat",
]


T = TypeVar("T")

Payload = Annotated[T, HTTPBody(embed=False)]
Body = Annotated[T, HTTPBody(embed=True)]
Path = Annotated[T, HTTPPath()]
Query = Annotated[T, HTTPQuery()]


class ImageFormat(StrEnum):
    PNG = "png"
    JPEG = "jpeg"
    JXL = "jxl"
    HEIC = "heic"
    WEBP = "webp"

    @property
    def content_type(self) -> str:
        return f"image/{self.value}"
