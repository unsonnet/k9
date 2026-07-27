from dataclasses import asdict, dataclass
from enum import StrEnum
from http import HTTPStatus
from inspect import Parameter, Signature, signature
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
    NotRequired,
    Protocol,
    Sequence,
    TypedDict,
    TypeGuard,
    Union,
    Unpack,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

import boto3
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler import Response as BaseResponse
from aws_lambda_powertools.event_handler.openapi.exceptions import (
    RequestValidationError,
)
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from types_boto3_cognito_idp import CognitoIdentityProviderClient
from types_boto3_cognito_idp.type_defs import AttributeTypeTypeDef

from ..config import GrantSpec, RouteSpec, is_set, missing, settings
from ..errors import DomainInvariantViolation
from .errors import InternalServerError, ServerError, UnprocessableEntity
from .responses import Response


class Role(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Caller:
    id: str
    name: str
    role: Role
    token: str

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN


class RouteOptions(TypedDict):
    cors: NotRequired[bool]
    compress: NotRequired[bool]
    cache_control: NotRequired[str]
    summary: NotRequired[str]
    description: NotRequired[str]
    responses: NotRequired[dict[int, str | OpenAPIResponse]]
    response_description: NotRequired[str]
    tags: NotRequired[list[str]]
    operation_id: NotRequired[str]
    include_in_schema: NotRequired[bool]
    security: NotRequired[list[dict[str, list[str]]]]
    openapi_extensions: NotRequired[dict[str, Any]]
    deprecated: NotRequired[bool]
    enable_validation: NotRequired[bool]
    custom_response_validation_http_code: NotRequired[int | HTTPStatus]
    middlewares: NotRequired[list[Callable[..., Any]]]


class RouteDecorator[R: BaseModel, T](Protocol):
    @overload
    def __call__(self, func: Callable[[], T]) -> Callable[[], T]: ...
    @overload
    def __call__(self, func: Callable[[R], T]) -> Callable[[R], T]: ...
    @overload
    def __call__(self, func: Callable[[Caller], T]) -> Callable[[Caller], T]: ...
    @overload
    def __call__(self, func: Callable[[Caller, R], T]) -> Callable[[Caller, R], T]: ...
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]: ...


class HttpResolver(APIGatewayHttpResolver):
    _idp: CognitoIdentityProviderClient
    _routes: list[RouteSpec]
    _grants: list[GrantSpec]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("enable_validation", True)
        super().__init__(*args, **kwargs)
        self._idp = boto3.client("cognito-idp", region_name=settings.aws_region)
        self._routes: list[RouteSpec] = []
        self._grants: list[GrantSpec] = []
        self.grant("cognito-idp:GetUser", resources=("cognito-user-pool",))
        super().exception_handler([RequestValidationError, PydanticValidationError])(
            lambda e: UnprocessableEntity(cause=e)
        )
        super().exception_handler(ServerError)(lambda e: e)
        super().exception_handler(Exception)(lambda e: InternalServerError(cause=e))

    def manifest(self) -> dict[str, Any]:
        return {
            "routes": [asdict(route) for route in self._routes],
            "grants": [asdict(grant) for grant in self._grants],
        }

    # ─── Authentication ───────────────────────────────────────────────────────────────

    @staticmethod
    def _unpack(attrs: Sequence[AttributeTypeTypeDef]) -> dict[str, str | None]:
        a = {kv["Name"].removeprefix("custom:"): kv.get("Value") for kv in attrs}
        a.setdefault("last_login_at", None)
        return a

    def caller(self) -> Caller:
        token = self.current_event.headers["authorization"].removeprefix("Bearer ")
        match self._idp.get_user(AccessToken=token):
            case {"UserAttributes": list(attrs)}:
                match self._unpack(attrs):
                    case {
                        "id": str(id),
                        "name": str(name),
                        "role": Role.USER | Role.ADMIN as role,
                    }:
                        return Caller(
                            id=id,
                            name=name,
                            role=Role(role),
                            token=token,
                        )
        raise DomainInvariantViolation("Unexpected cognito caller")

    # ─── Grants ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def _all[T](items: tuple[Any, ...], type: type[T]) -> TypeGuard[tuple[T]]:
        return all(isinstance(item, type) for item in items)

    @overload
    def grant(self, *grants: GrantSpec) -> None: ...

    @overload
    def grant(
        self,
        *actions: str,
        resources: tuple[str] = ("*",),
        effect: str = "allow",
    ) -> None: ...

    def grant(
        self,
        *raw: str | GrantSpec,
        resources: tuple[str] = ("*",),
        effect: str = "allow",
    ) -> None:
        match raw:
            case grants if self._all(grants, GrantSpec):
                self._grants.extend(grants)
            case actions if self._all(actions, str):
                self._grants.append(GrantSpec(effect, actions, resources))

    # ─── Routes ───────────────────────────────────────────────────────────────────────

    def route(  # type: ignore[override]
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        **options: Unpack[RouteOptions],
    ) -> RouteDecorator:
        def decorator[T](func: Callable[..., T]) -> Callable[..., T]:
            bound = signature(super(HttpResolver, self).route).bind_partial(**options)
            bound.apply_defaults()

            auth = next(iter(signature(func).parameters.values()), None) is Caller
            opid: str | None = bound.arguments["operation_id"]
            text: str | None = bound.arguments["summary"]
            tags: tuple[str, ...] = tuple(bound.arguments["tags"] or ())
            for item in (method,) if isinstance(method, str) else tuple(method):
                self._routes.append(
                    RouteSpec(
                        method=item.upper(),
                        rule=rule,
                        auth_required=auth,
                        operation_id=opid,
                        summary=text,
                        tags=tags,
                    )
                )

            responses = self._openapi(func, bound.arguments.pop("responses") or {})
            return super(HttpResolver, self).route(
                rule=rule,
                method=method,
                responses=responses,
                *bound.args,
                **bound.kwargs,
            )(self._expand(func))

        return decorator

    def get(self, rule: str, **options: Unpack[RouteOptions]) -> RouteDecorator:  # type: ignore[override]
        return self.route(rule=rule, method="GET", **options)

    def post(self, rule: str, **options: Unpack[RouteOptions]) -> RouteDecorator:  # type: ignore[override]
        return self.route(rule=rule, method="POST", **options)

    def put(self, rule: str, **options: Unpack[RouteOptions]) -> RouteDecorator:  # type: ignore[override]
        return self.route(rule=rule, method="PUT", **options)

    def patch(self, rule: str, **options: Unpack[RouteOptions]) -> RouteDecorator:  # type: ignore[override]
        return self.route(rule=rule, method="PATCH", **options)

    def delete(self, rule: str, **options: Unpack[RouteOptions]) -> RouteDecorator:  # type: ignore[override]
        return self.route(rule=rule, method="DELETE", **options)

    # ─── Request Model Expansion ──────────────────────────────────────────────────────

    @staticmethod
    def _is_union(T: type) -> bool:
        o = get_origin(T)
        return o is Union or (isinstance(o, type) and issubclass(o, UnionType))

    @classmethod
    def _openapi[T](
        cls,
        func: Callable[..., T],
        responses: dict[int, str | OpenAPIResponse],
    ) -> dict[int, OpenAPIResponse]:
        doc: dict[int, OpenAPIResponse] = {}
        models = signature(func).return_annotation
        for model in get_args(models) if cls._is_union(models) else (models,):
            respT = get_origin(model) or model
            if isinstance(respT, type) and issubclass(respT, Response):
                bodyT = (*get_args(model), NoneType)[0]
                doc[respT.status_code.value] = respT._openapi(bodyT)
        for code, desc in responses.items():
            if isinstance(desc, str):
                desc = doc.get(code, {}) | {"description": desc}
            doc[code] = desc
        return doc

    @classmethod
    def _wraps[T](cls, reqT: type, respT: type[T]):
        parameters = signature(reqT).parameters.values() if reqT is not NoneType else []
        annotations = get_type_hints(reqT, include_extras=True)
        bodies = set(
            bodyT
            for model in (get_args(respT) if cls._is_union(respT) else (respT,))
            for bodyT in (get_args(model) or (NoneType,))
        )
        sig = Signature(
            parameters=[
                param.replace(
                    default=missing
                    if param.default is not Parameter.empty
                    else param.default,
                    annotation=annotations[param.name],
                )
                for param in parameters
            ],
            return_annotation=BaseResponse[Union[*bodies]],
        )

        def decorator(wrapper: Callable[..., T]) -> Callable[..., T]:
            wrapper.__signature__ = sig  # type: ignore[attr-defined]
            wrapper.__annotations__ = annotations | {"return": sig.return_annotation}
            return wrapper

        return decorator

    def _expand[T](self, func: Callable[..., T]) -> Callable[..., T]:
        params = signature(func).parameters
        respT: type[T] = signature(func).return_annotation
        match params.get("caller", None), params.get("request", None):
            case None, None:

                @self._wraps(NoneType, respT)
                def wrapper() -> T:
                    return func()

            case Parameter(), None:

                @self._wraps(NoneType, respT)
                def wrapper() -> T:
                    return func(caller=self.caller())

            case Parameter(), Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                @self._wraps(reqT, respT)
                def wrapper(**kwargs) -> T:
                    kwargs = {k: v for k, v in kwargs.items() if is_set(v)}
                    request = reqT.model_validate(kwargs)
                    return func(caller=self.caller(), request=request)

            case None, Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                @self._wraps(reqT, respT)
                def wrapper(**kwargs) -> T:
                    kwargs = {k: v for k, v in kwargs.items() if is_set(v)}
                    request = reqT.model_validate(kwargs)
                    return func(request=request)

        return wrapper
