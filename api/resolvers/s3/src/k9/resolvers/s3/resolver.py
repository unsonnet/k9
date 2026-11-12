import re
from dataclasses import asdict
from inspect import Parameter, signature
from typing import Any, Callable, TypeGuard, overload
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.s3_event import S3Event
from aws_lambda_powertools.utilities.typing import LambdaContext
from k9.resolvers.base import LOG, EventSpec, GrantSpec
from pydantic import BaseModel

from .types import S3EventDecorator, S3EventRecord, S3Wrapper

__all__ = [
    "S3Resolver",
]


def pascal_case(s: str) -> str:
    return "".join(p.title() for p in s.split("_"))


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

    def event(self, rule: str, method: str) -> S3EventDecorator:
        if rule.count("*") > 1:
            raise ValueError("S3 event rules can contain at most one '*'")

        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            for r in self._unwrap(rule):
                self._events.append(EventSpec("s3", method, r))
                self._handlers[pascal_case(method), r] = self._expand(func)
            return func

        return decorator

    def created(self, rule: str) -> S3EventDecorator:
        return self.event(rule, method="OBJECT_CREATED")

    def removed(self, rule: str) -> S3EventDecorator:
        return self.event(rule, method="OBJECT_REMOVED")

    @staticmethod
    def _unwrap(rule: str) -> list[str]:
        if "{" not in rule and "}" not in rule:
            return [rule]
        if not (match := re.fullmatch(r"([^{}]*)\{([^{}]*)\}([^{}]*)", rule)):
            raise ValueError("S3 event rules support exactly one '{a,b}' group")
        head, body, tail = match.groups()
        if "" in (options := body.split(",")):
            raise ValueError("S3 event rule alternatives cannot be empty")
        return [f"{head}{option}{tail}" for option in options]

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
            event = record.event_name.partition(":")[0]
            key = unquote_plus(record.s3.get_object.key)
            handler = next(
                handler
                for (method, rule), handler in self._handlers.items()
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
