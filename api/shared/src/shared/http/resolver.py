from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
from http import HTTPStatus
from inspect import Parameter, signature
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    Callable,
    Mapping,
    Protocol,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response as BaseResponse
from aws_lambda_powertools.event_handler.api_gateway import (
    _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
)
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestValidationError,
)
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from ..errors import DomainInvalidTokens
from .errors import (
    InternalServerError,
    MethodNotAllowed,
    NotFound,
    ServerError,
    UnprocessableEntity,
)
from .requests import HTTPBody, HTTPPath, HTTPQuery
from .responses import Response

RequestModelT = TypeVar("RequestModelT", bound=BaseModel)
ReturnT = TypeVar("ReturnT")


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"


@dataclass
class Caller:
    id: str
    name: str
    role: Role
    token: str

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


class RouteDecorator(Protocol):
    @overload
    def __call__(self, func: Callable[[], ReturnT]) -> Callable[[], ReturnT]: ...

    @overload
    def __call__(
        self, func: Callable[[RequestModelT], ReturnT]
    ) -> Callable[[RequestModelT], ReturnT]: ...

    @overload
    def __call__(
        self, func: Callable[[Caller], ReturnT]
    ) -> Callable[[Caller], ReturnT]: ...

    @overload
    def __call__(
        self, func: Callable[[Caller, RequestModelT], ReturnT]
    ) -> Callable[[Caller, RequestModelT], ReturnT]: ...

    def __call__(self, func: Callable[..., ReturnT]) -> Callable[..., ReturnT]: ...


class HttpResolver(APIGatewayHttpResolver):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("enable_validation", True)
        super().__init__(*args, **kwargs)

        # Validation / routing error handling
        super().exception_handler(RequestValidationError)(
            lambda e: UnprocessableEntity(cause=e)
        )
        super().exception_handler(PydanticValidationError)(
            lambda e: UnprocessableEntity(cause=e)
        )
        super().exception_handler(NotFoundError)(self._handle_routing_error)
        super().exception_handler(ServerError)(lambda e: e)
        super().exception_handler(Exception)(lambda e: InternalServerError(cause=e))

    # ─── Auth Context ──────────────────────────────────────────────────────────

    def _claims(self) -> Mapping[str, Any]:
        try:
            return self.current_event.request_context.authorizer["jwt"]["claims"]
        except (AttributeError, KeyError, TypeError) as exc:
            raise DomainInvalidTokens("Missing JWT claims") from exc

    def _access_token(self) -> str:
        try:
            token = self.current_event.headers["authorization"]
        except (AttributeError, KeyError, TypeError) as exc:
            raise DomainInvalidTokens("Missing bearer token") from exc
        return token.removeprefix("Bearer ").strip()

    def _decode_id(self, xid: str) -> str:
        if not xid.startswith("id:"):
            raise DomainInvalidTokens(f"Invalid id format: {xid}")
        return xid.removeprefix("id:")

    def caller(self) -> Caller:
        match self._claims():
            case {
                "cognito:username": str(xid),
                "cognito:name": str(name),
                "custom:role": Role.USER | Role.ADMIN as role,
            }:
                return Caller(
                    id=self._decode_id(xid),
                    name=name,
                    role=role,
                    token=self._access_token(),
                )

        raise DomainInvalidTokens("Missing required JWT claims")

    # ─── Routes ────────────────────────────────────────────────────────────────

    def _handle_routing_error(self, exc: NotFoundError) -> NotFound | MethodNotAllowed:
        method = self.current_event.http_method.upper()
        path = self._remove_prefix(self.current_event.path)
        registered_routes = self._static_routes + self._dynamic_routes

        # If the path exists for a different method, respond 405; otherwise 404
        if any(
            route.method != method and route.rule.match(path)
            for route in registered_routes
        ):
            return MethodNotAllowed(cause=exc)

        return NotFound(cause=exc)

    def route(  # type: ignore[override]
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            parsed_responses = self._parse(func, responses or {})
            expanded_func = self._expand_request_model(func)
            normalized_func = self._normalize(expanded_func)

            return super(HttpResolver, self).route(
                rule=rule,
                method=method,
                cors=cors,
                compress=compress,
                cache_control=cache_control,
                summary=summary,
                description=description,
                responses=parsed_responses,
                response_description=response_description,
                tags=tags,
                operation_id=operation_id,
                include_in_schema=include_in_schema,
                security=security,
                openapi_extensions=openapi_extensions,
                deprecated=deprecated,
                enable_validation=enable_validation,
                custom_response_validation_http_code=custom_response_validation_http_code,
                middlewares=middlewares,
            )(normalized_func)

        return cast(RouteDecorator, decorator)

    # convenience methods delegate to route() with fixed HTTP verbs

    def get(  # type: ignore[override]
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        return self.route(
            rule=rule,
            method="GET",
            cors=cors,
            compress=compress,
            cache_control=cache_control,
            summary=summary,
            description=description,
            responses=responses,
            response_description=response_description,
            tags=tags,
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            security=security,
            openapi_extensions=openapi_extensions,
            deprecated=deprecated,
            enable_validation=enable_validation,
            custom_response_validation_http_code=custom_response_validation_http_code,
            middlewares=middlewares,
        )

    def post(  # type: ignore[override]
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        return self.route(
            rule=rule,
            method="POST",
            cors=cors,
            compress=compress,
            cache_control=cache_control,
            summary=summary,
            description=description,
            responses=responses,
            response_description=response_description,
            tags=tags,
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            security=security,
            openapi_extensions=openapi_extensions,
            deprecated=deprecated,
            enable_validation=enable_validation,
            custom_response_validation_http_code=custom_response_validation_http_code,
            middlewares=middlewares,
        )

    def put(  # type: ignore[override]
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        return self.route(
            rule=rule,
            method="PUT",
            cors=cors,
            compress=compress,
            cache_control=cache_control,
            summary=summary,
            description=description,
            responses=responses,
            response_description=response_description,
            tags=tags,
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            security=security,
            openapi_extensions=openapi_extensions,
            deprecated=deprecated,
            enable_validation=enable_validation,
            custom_response_validation_http_code=custom_response_validation_http_code,
            middlewares=middlewares,
        )

    def patch(  # type: ignore[override]
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        return self.route(
            rule=rule,
            method="PATCH",
            cors=cors,
            compress=compress,
            cache_control=cache_control,
            summary=summary,
            description=description,
            responses=responses,
            response_description=response_description,
            tags=tags,
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            security=security,
            openapi_extensions=openapi_extensions,
            deprecated=deprecated,
            enable_validation=enable_validation,
            custom_response_validation_http_code=custom_response_validation_http_code,
            middlewares=middlewares,
        )

    def delete(  # type: ignore[override]
        self,
        rule: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        responses: dict[int, str | OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        security: list[dict[str, list[str]]] | None = None,
        openapi_extensions: dict[str, Any] | None = None,
        deprecated: bool = False,
        enable_validation: bool | None = None,
        custom_response_validation_http_code: int | HTTPStatus | None = None,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> RouteDecorator:
        return self.route(
            rule=rule,
            method="DELETE",
            cors=cors,
            compress=compress,
            cache_control=cache_control,
            summary=summary,
            description=description,
            responses=responses,
            response_description=response_description,
            tags=tags,
            operation_id=operation_id,
            include_in_schema=include_in_schema,
            security=security,
            openapi_extensions=openapi_extensions,
            deprecated=deprecated,
            enable_validation=enable_validation,
            custom_response_validation_http_code=custom_response_validation_http_code,
            middlewares=middlewares,
        )

    # ─── Request Model Expansion ───────────────────────────────────────────────

    @staticmethod
    def _is_request_model(annotation: Any) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)

    @staticmethod
    def _param_marker(
        annotation: Any,
    ) -> HTTPBody | HTTPPath | HTTPQuery | None:
        if get_origin(annotation) is not Annotated:
            return None

        for meta in get_args(annotation)[1:]:
            if isinstance(meta, (HTTPBody, HTTPPath, HTTPQuery)):
                return meta

        return None

    @staticmethod
    def _field_default(model_cls: type[BaseModel], field_name: str) -> Any:
        field = model_cls.model_fields[field_name]
        if field.is_required():
            return Parameter.empty
        return field.default

    def _expand_request_model(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Supported handler forms:

        def handler() -> Response: ...

        def handler(request: SomeModel) -> Response: ...

        def handler(caller: Caller) -> Response: ...

        def handler(caller: Caller, request: SomeModel) -> Response: ...

        If a request model is present, expand it into the Powertools signature
        using Path / Query / Body annotations, but keep the handler API clean.
        """
        original_sig = signature(func)
        original_params = list(original_sig.parameters.values())

        if not original_params:
            # handler() -> Response
            return func

        if len(original_params) not in {1, 2}:
            raise TypeError(
                f"{func.__name__} must accept either no parameters, exactly one "
                "Caller or request model parameter, or (caller, request)"
            )

        original_hints = get_type_hints(func, include_extras=True)

        # Determine caller / request roles for the parameters
        caller_param = None
        request_param = None

        if len(original_params) == 2:
            # (caller, request)
            caller_param = original_params[0]
            caller_type = original_hints.get(caller_param.name, caller_param.annotation)
            if caller_type is not Caller:
                raise TypeError(
                    f"{func.__name__}.{caller_param.name} must be annotated as Caller"
                )
            request_param = original_params[1]
        else:
            # Single parameter: either Caller or request model
            only_param = original_params[0]
            only_type = original_hints.get(only_param.name, only_param.annotation)
            if only_type is Caller:
                caller_param = only_param
            else:
                request_param = only_param

        # If there is no request param, this is handler(caller: Caller)
        if request_param is None:

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(self.caller())

            wrapper.__signature__ = original_sig  # type: ignore[attr-defined]
            wrapper.__annotations__ = dict(getattr(func, "__annotations__", {}))
            return wrapper

        # From here on, we know there is a request model parameter
        request_model = original_hints.get(
            request_param.name,
            request_param.annotation,
        )

        if not self._is_request_model(request_model):
            raise TypeError(
                f"{func.__name__}.{request_param.name} must be annotated with a "
                "Pydantic request model"
            )

        model_cls: type[BaseModel] = request_model
        model_hints = get_type_hints(model_cls, include_extras=True)

        expanded_params: list[Parameter] = []
        expanded_field_names: list[str] = []

        for field_name in model_cls.model_fields:
            field_annotation = model_hints.get(field_name)
            if field_annotation is None:
                raise TypeError(
                    f"{model_cls.__name__}.{field_name} is missing an annotation"
                )

            marker = self._param_marker(field_annotation)
            if marker is None:
                raise TypeError(
                    f"{model_cls.__name__}.{field_name} must be annotated as "
                    "Path[T], Query[T], or Body[T]"
                )

            expanded_params.append(
                Parameter(
                    name=field_name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    default=self._field_default(model_cls, field_name),
                    annotation=field_annotation,
                )
            )
            expanded_field_names.append(field_name)

        expanded_sig = original_sig.replace(parameters=expanded_params)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = expanded_sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            request = model_cls(
                **{
                    field_name: bound.arguments[field_name]
                    for field_name in expanded_field_names
                    if field_name in bound.arguments
                }
            )

            if caller_param is not None:
                return func(self.caller(), request)
            return func(request)

        wrapper.__signature__ = expanded_sig  # type: ignore[attr-defined]
        wrapper.__annotations__ = {
            name: param.annotation
            for name, param in expanded_sig.parameters.items()
            if param.annotation is not Parameter.empty
        }
        wrapper.__annotations__["return"] = original_sig.return_annotation

        setattr(wrapper, "__original_handler__", func)
        setattr(wrapper, "__request_model__", model_cls)
        setattr(wrapper, "__request_parameter__", request_param.name)

        return wrapper

    # ─── OpenAPI Response Parsing ──────────────────────────────────────────────

    @classmethod
    def _parse(
        cls,
        func: Callable[..., Any],
        responses: dict[int, str | OpenAPIResponse],
    ) -> dict[int, OpenAPIResponse] | None:
        result: dict[int, OpenAPIResponse] = {}

        annotation = get_type_hints(func, include_extras=True).get("return")

        for response_cls, body_type in cls._extract(annotation):
            result[response_cls.status_code.value] = response_cls._openapi(body_type)

        for status, value in responses.items():
            if isinstance(value, str):
                result.setdefault(status, {})["description"] = value
            else:
                result[status] = value

        return result or None

    @classmethod
    def _body(cls, response_cls: type[Response[Any]]) -> type[Any]:
        # Try generic metadata first
        meta = getattr(response_cls, "__pydantic_generic_metadata__", None)
        args = meta.get("args", ()) if meta else ()
        if args:
            return args[0]

        # Walk MRO to find a generic base Response[T]
        for candidate in (response_cls, *response_cls.__mro__[1:]):
            if not isinstance(candidate, type):
                continue

            for base in getattr(candidate, "__orig_bases__", ()):
                origin = get_origin(base)
                if origin is None or not isinstance(origin, type):
                    continue
                if not issubclass(origin, Response):
                    continue

                args = get_args(base)
                if args:
                    return args[0]

            # Some tools put generic metadata on intermediate classes
            meta = getattr(candidate, "__pydantic_generic_metadata__", None)
            args = meta.get("args", ()) if meta else ()
            if args:
                return args[0]

        return NoneType

    @classmethod
    def _extract(
        cls,
        annotation: Any,
    ) -> list[tuple[type[Response[Any]], type[Any]]]:
        if annotation is None:
            return []

        origin = get_origin(annotation)

        if origin is Union or origin is UnionType:
            result: list[tuple[type[Response[Any]], type[Any]]] = []
            for arg in get_args(annotation):
                result.extend(cls._extract(arg))
            return result

        if (
            origin is not None
            and isinstance(origin, type)
            and issubclass(origin, Response)
        ):
            args = get_args(annotation)
            body_type = args[0] if args else NoneType
            return [(origin, body_type)]

        if isinstance(annotation, type) and issubclass(annotation, Response):
            return [(annotation, cls._body(annotation))]

        return []

    @classmethod
    def _union(cls, annotation: Any) -> Any:
        all_body_types = [body_type for _, body_type in cls._extract(annotation)]
        has_none = any(bt is NoneType for bt in all_body_types)
        body_types = [bt for bt in all_body_types if bt is not NoneType]

        if not body_types:
            return NoneType

        union: Any = body_types[0]
        for body_type in body_types[1:]:
            union = union | body_type

        if has_none:
            union = union | NoneType
        return union

    @classmethod
    def _normalize(cls, func: Callable[..., Any]) -> Callable[..., Any]:
        original_annotation = get_type_hints(func, include_extras=True).get("return")
        normalized_return = BaseResponse[cls._union(original_annotation)]
        sig = signature(func).replace(return_annotation=normalized_return)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper.__signature__ = sig  # type: ignore[attr-defined]
        wrapper.__annotations__ = dict(getattr(func, "__annotations__", {}))
        wrapper.__annotations__["return"] = normalized_return
        setattr(wrapper, "__original_return_annotation__", original_annotation)

        return wrapper
