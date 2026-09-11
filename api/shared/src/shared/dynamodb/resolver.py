from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from inspect import Parameter, signature
from typing import Any, Protocol, TypeGuard, overload

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
    StreamRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from ..config import EventSpec, GrantSpec

__all__ = [
    "DynamoDBResolver",
]


LOG = Logger()


class EventDecorator[R: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


@dataclass(frozen=True, slots=True)
class DynamoDBWrapper(Mapping):
    _data: StreamRecord

    def __getitem__(self, key: str) -> dict:
        return getattr(self._data, key)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class DynamoDBResolver:
    _processor: BatchProcessor
    _grants: list[GrantSpec]
    _events: list[EventSpec]
    _handlers: dict[tuple[str, str], Callable[[DynamoDBRecord], Any]]

    def __init__(self) -> None:
        super().__init__()
        self._processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
        self._handlers = {}

    def manifest(self) -> dict[str, Any]:
        return {
            "grants": [asdict(grant) for grant in self._grants],
            "events": [asdict(route) for route in self._events],
        }

    # ──── Grants ────

    @staticmethod
    def _all[T](items: tuple[Any, ...], type: type[T]) -> TypeGuard[tuple[T, ...]]:
        return all(isinstance(item, type) for item in items)

    @overload
    def grant(self, *grants: GrantSpec) -> None: ...

    @overload
    def grant(
        self,
        *actions: str,
        resources: tuple[str, ...] = ("*",),
        effect: str = "allow",
    ) -> None: ...

    def grant(
        self,
        *raw: str | GrantSpec,
        resources: tuple[str, ...] = ("*",),
        effect: str = "allow",
    ) -> None:
        match raw:
            case grants if self._all(grants, GrantSpec):
                self._grants.extend(grants)
            case actions if self._all(actions, str):
                self._grants.append(GrantSpec(effect, actions, resources))

    # ──── Events ────

    def event(self, rule: str, method: str) -> EventDecorator:
        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            self._events.append(EventSpec(method, rule))
            self._handlers[method, rule] = self._expand(func)
            return func

        return decorator

    def insert(self, rule: str) -> EventDecorator:
        return self.event(rule, method="INSERT")

    def modify(self, rule: str) -> EventDecorator:
        return self.event(rule, method="MODIFY")

    def remove(self, rule: str) -> EventDecorator:
        return self.event(rule, method="REMOVE")

    # ──── Model Expansion ────

    @classmethod
    def _expand[T](cls, func: Callable[..., T]) -> Callable[[DynamoDBRecord], T]:
        params = signature(func).parameters
        match params.get("request", None):
            case None:

                def wrapper(record: DynamoDBRecord) -> T:
                    return func()

            case Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                def wrapper(record: DynamoDBRecord) -> T:
                    request = reqT.model_validate(DynamoDBWrapper(record.dynamodb))  # type: ignore
                    return func(request=request)

        return wrapper

    # ──── Resolver ────

    def _handle(self, record: DynamoDBRecord) -> Any:
        try:
            method: str = record.event_name.name  # type: ignore
            payload = record.dynamodb
            rule: str = (payload.new_image or payload.old_image).get("type")  # type: ignore
            handler = self._handlers[method, rule]
        except Exception as exc:
            LOG.error(
                "Failed to resolve handler for event record",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            raise

        try:
            return handler(record)
        except Exception as exc:
            LOG.error(
                "Failed to process event record",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            raise

    def resolve(
        self,
        event: dict[str, Any],
        context: LambdaContext,
    ) -> Mapping[str, Any]:
        return process_partial_response(
            event=event,
            record_handler=self._handle,
            processor=self._processor,
            context=context,
        )
