#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Product provider module."""

from .base import ProductDBProvider, NoopProductDBProvider
from .dynamo import DynamoProductDBProvider

__all__ = [
    "ProductDBProvider",
    "NoopProductDBProvider",
    "DynamoProductDBProvider",
]
