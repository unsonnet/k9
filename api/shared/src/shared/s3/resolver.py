from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from inspect import Parameter, signature
from typing import Any, Protocol, TypeGuard, overload
from urllib.parse import unquote_plus

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes.s3_event import S3Event, S3EventRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from ..config import EventSpec, GrantSpec

__all__ = [
    "S3Resolver",
]


LOG = Logger()


class EventDecorator[R: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


@dataclass(frozen=True, slots=True)
class S3Wrapper(Mapping):
    _data: Mapping[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class S3Resolver:
    _grants: list[GrantSpec]
    _events: list[EventSpec]
    _handlers: dict[tuple[str, str], Callable[[S3EventRecord], Any]]

    def __init__(self) -> None:
        super().__init__()
        self._grants = []
        self._events = []
        self._handlers = {}

    def manifest(self) -> dict[str, Any]:
        return {
            "grants": [asdict(grant) for grant in self._grants],
            "events": [asdict(event) for event in self._events],
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
        if rule.count("*") > 1:
            raise ValueError("S3 event rules can contain at most one '*'")

        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            self._events.append(EventSpec("s3", method, rule))
            self._handlers[method, rule] = self._expand(func)
            return func

        return decorator

    def created(self, rule: str) -> EventDecorator:
        return self.event(rule, method="Object_Created")

    def removed(self, rule: str) -> EventDecorator:
        return self.event(rule, method="Object_Removed")

    # ──── Model Expansion ────

    @classmethod
    def _expand[T](cls, func: Callable[..., T]) -> Callable[[S3EventRecord], T]:
        params = signature(func).parameters
        match params.get("request", None):
            case None:

                def wrapper(record: S3EventRecord) -> T:
                    return func()

            case Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                def wrapper(record: S3EventRecord) -> T:
                    request = reqT.model_validate(S3Wrapper(record.s3.get_object))
                    return func(request=request)

        return wrapper

    # ──── Resolver ────

    @staticmethod
    def _matches(key: str, rule: str) -> bool:
        prefix, _, suffix = rule.partition("*")
        return key.startswith(prefix) and key.endswith(suffix)

    def _handle(self, record: S3EventRecord) -> Any:
        try:
            method = record.event_name.partition(":")[0]
            key = unquote_plus(record.s3.get_object.key)
            handler = next(
                handler
                for (event, rule), handler in self._handlers.items()
                if event == method and self._matches(key, rule)
            )
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
    ) -> None:
        for record in S3Event(event).records:
            self._handle(record)
