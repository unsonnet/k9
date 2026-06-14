from enum import StrEnum

from .errors import ClientError, ServerError
from .requests import Body, Path, Query
from .resolver import HttpResolver
from .responses import Response


class ImageMIMEType(StrEnum):
    JPEGXL = "image/jxl"


__all__ = [
    "HttpResolver",
    "Body",
    "Path",
    "Query",
    "Response",
    "ClientError",
    "ServerError",
    "ImageMIMEType",
]
