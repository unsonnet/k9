from dataclasses import asdict
from inspect import signature
from typing import Any, Callable, Mapping, TypeGuard, overload

from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from k9.resolvers.base import LOG, EventSpec, GrantSpec
from k9.shared.config import is_set, missing
from pydantic import BaseModel

from .types import MISSING_PARAM, DynamoDBEventDecorator, DynamoDBRecord

__all__ = [
    "DynamoDBResolver",
]


class DynamoDBResolver:
    _processor: BatchProcessor
    _grants: list[GrantSpec]
    _events: list[EventSpec]
    _handlers: dict[tuple[str, str], Callable[[dict, dict], Any]]

    def __init__(self) -> None:
        super().__init__()
        self._processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
        self._grants = []
        self._events = []
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

    def event(self, rule: str, method: str) -> DynamoDBEventDecorator:
        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            self._events.append(EventSpec("dynamodb", method, rule))
            self._handlers[method, rule] = self._expand(func)
            return func

        return decorator

    def insert(self, rule: str) -> DynamoDBEventDecorator:
        return self.event(rule, method="INSERT")

    def modify(self, rule: str) -> DynamoDBEventDecorator:
        return self.event(rule, method="MODIFY")

    def remove(self, rule: str) -> DynamoDBEventDecorator:
        return self.event(rule, method="REMOVE")

    # ──── Model Expansion ────

    @staticmethod
    def _expand[T](func: Callable[..., T]) -> Callable[[dict, dict], T]:
        params = signature(func).parameters
        keyT: type[str] | missing = params.get("key", MISSING_PARAM).annotation
        newT: type[BaseModel] | missing = params.get("new", MISSING_PARAM).annotation
        oldT: type[BaseModel] | missing = params.get("old", MISSING_PARAM).annotation

        def wrapper(new: dict, old: dict) -> T:
            kwargs = {}
            if is_set(keyT):
                kwargs["key"] = (new or old)["key"]["key"]
            if is_set(newT):
                new.pop("key")
                kwargs["new"] = newT.model_validate(new)
            if is_set(oldT):
                old.pop("key")
                kwargs["old"] = oldT.model_validate(old)
            return func(**kwargs)

        return wrapper

    # ──── Resolver ────

    def _handle(self, record: DynamoDBRecord) -> Any:
        event, payload = record.event_name, record.dynamodb
        assert event is not None and payload is not None
        try:
            method = event.name
            rule = (payload.new_image or payload.old_image)["key"]["type"]
            handler = self._handlers[method, rule]
        except Exception as exc:
            info = (type(exc), exc, exc.__traceback__)
            LOG.error("Failed to resolve handler for event record", exc_info=info)
            raise
        try:
            return handler(payload.new_image, payload.old_image)
        except Exception as exc:
            info = (type(exc), exc, exc.__traceback__)
            LOG.error("Failed to process event record", exc_info=info)
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
