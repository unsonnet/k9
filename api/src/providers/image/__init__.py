#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Image provider module."""

from .base import ImageDBProvider, NoopImageDBProvider
from .s3 import S3ImageDBProvider

__all__ = [
    "ImageDBProvider",
    "NoopImageDBProvider",
    "S3ImageDBProvider",
]
