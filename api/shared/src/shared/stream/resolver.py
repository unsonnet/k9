from collections.abc import Callable, Mapping
from dataclasses import asdict
from enum import StrEnum
from inspect import Parameter, signature
from typing import (
    Annotated,
    Any,
    Protocol,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import AliasChoices, AliasPath, BaseModel, TypeAdapter

from ..config import GrantSpec
from .requests import StreamKeys, StreamNewImage, StreamOldImage, StreamRecord

RequestModelT = TypeVar("RequestModelT", bound=BaseModel)
ReturnT = TypeVar("ReturnT")


class EventName(StrEnum):
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    REMOVE = "REMOVE"


class RouteDecorator(Protocol):
    def __call__(
        self, func: Callable[[RequestModelT], ReturnT]
    ) -> Callable[[RequestModelT], ReturnT]: ...


StreamMarker = StreamNewImage | StreamOldImage | StreamKeys | StreamRecord


class DynamoDBStreamResolver:
    def __init__(self) -> None:
        self._processor = BatchProcessor(event_type=EventType.DynamoDBStreams)
        self._handlers: dict[EventName, Callable[[Any], Any]] = {}
        self._models: dict[EventName, type[BaseModel]] = {}
        self._grant_specs: list[GrantSpec] = []

    # ─── Manifest ─────────────────────────────────────────────────────────────────────

    @property
    def grants(self) -> tuple[GrantSpec, ...]:
        return tuple(self._grant_specs)

    def grant(self, *grants: GrantSpec) -> None:
        self._grant_specs.extend(grants)

    def manifest(self) -> dict[str, Any]:
        return {
            "grants": [asdict(grant) for grant in self._grant_specs],
        }

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
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            model_cls = self._request_model(func)

            self._handlers[event_name] = func
            self._models[event_name] = model_cls

            return func

        return cast(RouteDecorator, decorator)

    # ─── Request Model Inspection ─────────────────────────────────────────────────────

    @staticmethod
    def _is_request_model(annotation: Any) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)

    @classmethod
    def _request_model(cls, func: Callable[..., Any]) -> type[BaseModel]:
        sig = signature(func)
        params = list(sig.parameters.values())

        if len(params) != 1:
            raise TypeError(
                f"{func.__name__} must accept exactly one Pydantic request model"
            )

        param = params[0]

        if param.kind not in {
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        }:
            raise TypeError(f"{func.__name__}.{param.name} must be a normal parameter")

        hints = get_type_hints(func, include_extras=True)
        annotation = hints.get(param.name, param.annotation)

        if not cls._is_request_model(annotation):
            raise TypeError(
                f"{func.__name__}.{param.name} must be annotated with a "
                "Pydantic request model"
            )

        return annotation

    @staticmethod
    def _param_marker(annotation: Any) -> StreamMarker | None:
        if get_origin(annotation) is not Annotated:
            return None

        for meta in get_args(annotation)[1:]:
            if isinstance(
                meta,
                (
                    StreamNewImage,
                    StreamOldImage,
                    StreamKeys,
                    StreamRecord,
                ),
            ):
                return meta

        return None

    @staticmethod
    def _param_type(annotation: Any) -> Any:
        if get_origin(annotation) is Annotated:
            return get_args(annotation)[0]
        return annotation

    # ─── Pydantic Alias Handling ──────────────────────────────────────────────────────

    @staticmethod
    def _alias_path_values(alias: AliasPath) -> list[str | int]:
        return list(alias.convert_to_aliases())

    @classmethod
    def _field_keys(
        cls,
        *,
        model_cls: type[BaseModel],
        field_name: str,
    ) -> list[str | int]:
        field = model_cls.model_fields[field_name]

        if isinstance(field.validation_alias, str):
            return [field.validation_alias]

        if isinstance(field.validation_alias, AliasPath):
            return cls._alias_path_values(field.validation_alias)

        if isinstance(field.validation_alias, AliasChoices):
            choices = field.validation_alias.convert_to_aliases()
            if not choices:
                return [field_name]

            first = choices[0]

            if isinstance(first, str):
                return [first]

            return list(first)

        if isinstance(field.alias, str):
            return [field.alias]

        return [field_name]

    @staticmethod
    def _get_path(source: Mapping[str, Any], keys: list[str | int]) -> Any:
        value: Any = source

        for key in keys:
            if isinstance(value, Mapping):
                try:
                    value = value[key]
                except KeyError as exc:
                    path = ".".join(str(part) for part in keys)
                    raise ValueError(f"Stream source missing field {path!r}") from exc
            elif isinstance(value, list) and isinstance(key, int):
                try:
                    value = value[key]
                except IndexError as exc:
                    path = ".".join(str(part) for part in keys)
                    raise ValueError(f"Stream source missing field {path!r}") from exc
            else:
                path = ".".join(str(part) for part in keys)
                raise TypeError(f"Stream source cannot resolve path {path!r}")

        return value

    # ─── Stream Source Extraction ─────────────────────────────────────────────────────

    @staticmethod
    def _mapping(value: Any, source: str) -> Mapping[str, Any]:
        if value is None:
            raise ValueError(f"Stream record missing {source}")

        if not isinstance(value, Mapping):
            raise TypeError(f"Stream {source} must be a mapping")

        return value

    def _source_for(self, marker: StreamMarker, record: DynamoDBRecord) -> Any:
        if isinstance(marker, StreamRecord):
            return record

        if record.dynamodb is None:
            raise ValueError("Stream record missing dynamodb payload")

        if isinstance(marker, StreamNewImage):
            return self._mapping(record.dynamodb.new_image, "NewImage")

        if isinstance(marker, StreamOldImage):
            return self._mapping(record.dynamodb.old_image, "OldImage")

        if isinstance(marker, StreamKeys):
            return self._mapping(record.dynamodb.keys, "Keys")

        raise TypeError(f"Unsupported stream marker: {marker!r}")

    def _value_for_field(
        self,
        *,
        model_cls: type[BaseModel],
        field_name: str,
        field_type: Any,
        marker: StreamMarker,
        record: DynamoDBRecord,
    ) -> Any:
        source = self._source_for(marker, record)

        if isinstance(marker, StreamRecord):
            return TypeAdapter(field_type).validate_python(source)

        if self._is_request_model(field_type):
            return TypeAdapter(field_type).validate_python(source)

        keys = self._field_keys(model_cls=model_cls, field_name=field_name)

        return self._get_path(source, keys)

    def _build_request(
        self,
        model_cls: type[BaseModel],
        record: DynamoDBRecord,
    ) -> BaseModel:
        model_hints = get_type_hints(model_cls, include_extras=True)
        values: dict[str, Any] = {}

        for field_name in model_cls.model_fields:
            annotation = model_hints.get(field_name)

            if annotation is None:
                raise TypeError(
                    f"{model_cls.__name__}.{field_name} is missing an annotation"
                )

            marker = self._param_marker(annotation)

            if marker is None:
                raise TypeError(
                    f"{model_cls.__name__}.{field_name} must be annotated as "
                    "NewImage[T], OldImage[T], Keys[T], or Record[T]"
                )

            field_type = self._param_type(annotation)

            values[field_name] = self._value_for_field(
                model_cls=model_cls,
                field_name=field_name,
                field_type=field_type,
                marker=marker,
                record=record,
            )

        return model_cls.model_validate(values)

    # ─── Resolve ──────────────────────────────────────────────────────────────────────

    def _handle_record(self, record: DynamoDBRecord) -> None:
        event_name = EventName(record.event_name)

        try:
            handler = self._handlers[event_name]
            model_cls = self._models[event_name]
        except KeyError as exc:
            raise RuntimeError(f"No handler registered for {event_name}") from exc

        request = self._build_request(model_cls, record)
        handler(request)

    def resolve(
        self,
        event: dict[str, Any],
        context: LambdaContext,
    ) -> Mapping[str, Any]:
        return process_partial_response(
            event=event,
            record_handler=self._handle_record,
            processor=self._processor,
            context=context,
        )
