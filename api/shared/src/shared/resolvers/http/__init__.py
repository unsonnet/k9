from enum import StrEnum

from .errors import ClientError, ServerError
from .requests import Body, Path, Query
from .resolver import Caller, HttpResolver, Role
from .responses import Response


class ImageMIMEType(StrEnum):
    JPEGXL = "image/jxl"


__all__ = [
    "Role",
    "Caller",
    "HttpResolver",
    "Body",
    "Path",
    "Query",
    "Response",
    "ClientError",
    "ServerError",
    "ImageMIMEType",
]
