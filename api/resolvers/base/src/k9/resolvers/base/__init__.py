from aws_lambda_powertools import Logger

from .types import EventSpec, GrantSpec, RouteSpec

__all__ = [
    "EventSpec",
    "GrantSpec",
    "LOG",
    "RouteSpec",
]

LOG = Logger()
