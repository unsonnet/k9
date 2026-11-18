from aws_lambda_powertools import Logger

from .register import load_apis
from .types import EventSpec, GrantSpec, RouteSpec

__all__ = [
    "EventSpec",
    "GrantSpec",
    "load_apis",
    "LOG",
    "RouteSpec",
]

LOG = Logger()
