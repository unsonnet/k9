import re

from k9.types.base import ValidatedStr

__all__ = [
    "S3Url",
]


class S3Url(ValidatedStr):
    _pattern = re.compile(r"s3://[^/?#@:\s]+/[^?#\s]+")
