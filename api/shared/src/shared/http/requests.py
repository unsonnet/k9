from typing import Annotated, TypeVar

from aws_lambda_powertools.event_handler.openapi.params import Body as HTTPBody
from aws_lambda_powertools.event_handler.openapi.params import Path as HTTPPath
from aws_lambda_powertools.event_handler.openapi.params import Query as HTTPQuery

T = TypeVar("T")

Body = Annotated[T, HTTPBody(embed=True)]
Path = Annotated[T, HTTPPath()]
Query = Annotated[T, HTTPQuery()]

__all__ = [
    "Body",
    "Path",
    "Query",
]
