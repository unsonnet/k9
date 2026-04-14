from typing import Annotated

from aws_lambda_powertools.event_handler.openapi.params import Body as BaseBody

type Body[T] = Annotated[T, BaseBody()]
