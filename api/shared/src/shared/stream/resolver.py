from collections.abc import Callable, Mapping
from dataclasses import asdict
from enum import StrEnum
from inspect import Parameter, signature
from typing import (
    Annotated,
    Any,
    Protocol,
    TypeGuard,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from ..config import GrantSpec
from .requests import StreamKeys, StreamNewImage, StreamOldImage, StreamRecord

LOG = Logger()


class EventName(StrEnum):
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"


StreamMarker = StreamNewImage | StreamOldImage | StreamKeys | StreamRecord


class RouteDecorator[R: BaseModel, T](Protocol):
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...


class DynamoDBStreamResolver:
    _processor: BatchProcessor
    _handlers: dict[EventName, Callable[[DynamoDBRecord], Any]]
    _grants: list[GrantSpec]

    def __init__(self) -> None:
        self._processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
        self._handlers = {}
        self._grants = []

    def manifest(self) -> dict[str, Any]:
        return {
            "grants": [asdict(grant) for grant in self._grants],
        }

    # ─── Grants ───────────────────────────────────────────────────────────────────────

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

    # ─── Routes ───────────────────────────────────────────────────────────────────────

    @property
    def insert(self) -> RouteDecorator:
        return self.route(EventName.INSERT)

    @property
    def modify(self) -> RouteDecorator:
        return self.route(EventName.MODIFY)

    @property
    def remove(self) -> RouteDecorator:
        return self.route(EventName.REMOVE)

    def route(self, event_name: EventName) -> RouteDecorator:
        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            self._handlers[event_name] = self._expand(func)
            return func

        return decorator

    # ─── Request Model Expansion ──────────────────────────────────────────────────────

    @staticmethod
    def _marker(annotation: Any) -> StreamMarker:
        if get_origin(annotation) is Annotated:
            for metadata in get_args(annotation)[1:]:
                if isinstance(
                    metadata,
                    (
                        StreamNewImage,
                        StreamOldImage,
                        StreamKeys,
                        StreamRecord,
                    ),
                ):
                    return metadata

        raise TypeError(
            "Stream request fields must be annotated with "
            "NewImage[T], OldImage[T], Keys[T], or Record[T]"
        )

    @staticmethod
    def _source(
        marker: StreamMarker,
        record: DynamoDBRecord,
    ) -> Any:
        if isinstance(marker, StreamRecord):
            return record

        if record.dynamodb is None:
            raise ValueError("Stream record missing dynamodb payload")

        match marker:
            case StreamNewImage():
                source = record.dynamodb.new_image
            case StreamOldImage():
                source = record.dynamodb.old_image
            case StreamKeys():
                source = record.dynamodb.keys

        if source is None:
            raise ValueError(
                f"Stream record missing {type(marker).__name__.removeprefix('Stream')}"
            )

        return source

    @classmethod
    def _request(
        cls,
        reqT: type[BaseModel],
        record: DynamoDBRecord,
    ) -> BaseModel:
        annotations = get_type_hints(reqT, include_extras=True)

        return reqT.model_validate(
            {
                name: cls._source(cls._marker(annotations[name]), record)
                for name in reqT.model_fields
            }
        )

    @classmethod
    def _expand[T](
        cls,
        func: Callable[..., T],
    ) -> Callable[[DynamoDBRecord], T]:
        params = signature(func).parameters

        match params.get("request", None):
            case Parameter() as reqP if len(params) == 1:
                reqT = get_type_hints(func, include_extras=True)["request"]

                if not isinstance(reqT, type) or not issubclass(reqT, BaseModel):
                    raise TypeError(
                        f"{func.__name__}.{reqP.name} must be a Pydantic model"
                    )

                def wrapper(record: DynamoDBRecord) -> T:
                    request = cls._request(reqT, record)
                    return func(request=request)

                return wrapper

        raise TypeError(
            f"{func.__name__} must accept exactly one Pydantic parameter "
            "named 'request'"
        )

    # ─── Resolution ───────────────────────────────────────────────────────────────────

    def _handle(self, record: DynamoDBRecord) -> Any:
        if record.event_name is None:
            raise ValueError("Stream record missing event name")
        event_name = EventName(record.event_name.name)

        try:
            handler = self._handlers[event_name]
        except KeyError as exc:
            raise RuntimeError(f"No handler registered for {event_name}") from exc

        try:
            return handler(record)
        except Exception as exc:
            LOG.error(
                "Stream record processing failed",
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
