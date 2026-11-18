from dataclasses import asdict
from inspect import Parameter, Signature, signature
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
    Iterable,
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
from k9.resolvers.base import GrantSpec, RouteSpec
from k9.shared.config import settings
from k9.types.common import Caller, is_set, missing
from k9.types.errors import DomainInvariantViolation
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from types_boto3_cognito_idp import CognitoIdentityProviderClient
from types_boto3_cognito_idp.type_defs import AttributeTypeTypeDef

from .errors import InternalServerError, ServerError, UnprocessableEntity
from .responses import Response
from .types import CALLER_PARAM, HttpRouteDecorator, HttpRouteOptions

__all__ = [
    "HttpResolver",
]


class HttpResolver(APIGatewayHttpResolver):
    _idp: CognitoIdentityProviderClient
    _grants: list[GrantSpec]
    _routes: list[RouteSpec]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("enable_validation", True)
        super().__init__(*args, **kwargs)
        self._idp = boto3.client("cognito-idp", region_name=settings.aws_region)
        self._grants = []
        self._routes = []
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

    # ──── Routes ────

    def route(  # type: ignore[override]
        self,
        rule: str,
        method: str | list[str] | tuple[str],
        **options: Unpack[HttpRouteOptions],
    ) -> HttpRouteDecorator:
        def decorator[T: Response](func: Callable[..., T]) -> Callable[..., T]:
            bound = signature(super(HttpResolver, self).route).bind_partial(**options)
            bound.apply_defaults()

            auth = signature(func).parameters.get("caller", None) == CALLER_PARAM
            opid: str | None = bound.arguments["operation_id"]
            text: str | None = bound.arguments["summary"]
            tags: tuple[str, ...] = tuple(bound.arguments["tags"] or ())
            for item in (method,) if isinstance(method, str) else tuple(method):
                self._routes.append(
                    RouteSpec(
                        method=item,
                        rule=rule,
                        auth_required=auth,
                        operation_id=opid,
                        summary=text,
                        tags=tags,
                    )
                )

            responses = self._openapi(func, bound.arguments.pop("responses") or {})
            super(HttpResolver, self).route(
                rule=rule,
                method=method,
                responses=responses,
                *bound.args,
                **bound.kwargs,
            )(self._expand(func))
            return func

        return decorator

    def get(  # type: ignore[override]
        self, rule: str, **options: Unpack[HttpRouteOptions]
    ) -> HttpRouteDecorator:
        return self.route(rule=rule, method="GET", **options)

    def post(  # type: ignore[override]
        self, rule: str, **options: Unpack[HttpRouteOptions]
    ) -> HttpRouteDecorator:
        return self.route(rule=rule, method="POST", **options)

    def put(  # type: ignore[override]
        self, rule: str, **options: Unpack[HttpRouteOptions]
    ) -> HttpRouteDecorator:
        return self.route(rule=rule, method="PUT", **options)

    def patch(  # type: ignore[override]
        self, rule: str, **options: Unpack[HttpRouteOptions]
    ) -> HttpRouteDecorator:
        return self.route(rule=rule, method="PATCH", **options)

    def delete(  # type: ignore[override]
        self, rule: str, **options: Unpack[HttpRouteOptions]
    ) -> HttpRouteDecorator:
        return self.route(rule=rule, method="DELETE", **options)

    # ──── Authentication ────

    @staticmethod
    def _parse(attrs: Iterable[AttributeTypeTypeDef]) -> dict[str, str | None]:
        a = {kv["Name"].removeprefix("custom:"): kv.get("Value") for kv in attrs}
        a.setdefault("last_login_at", None)
        return a

    def caller(self) -> Caller:
        token = self.current_event.headers["authorization"].removeprefix("Bearer ")
        match self._idp.get_user(AccessToken=token):
            case {"UserAttributes": list(attrs)}:
                return Caller.model_validate(self._parse(attrs) | {"token": token})
        raise DomainInvariantViolation("Unexpected cognito caller")

    # ──── Model Expansion ────

    @staticmethod
    def _unpack(respT: type[Response]) -> Iterable[type[Response]]:
        o = get_origin(respT)
        if o is Union or (isinstance(o, type) and issubclass(o, UnionType)):
            yield from get_args(respT)
        else:
            yield respT

    @staticmethod
    def _body(rT: type[Response]) -> type[BaseModel] | type[None]:
        r: type[Response] = get_origin(rT) or rT
        T = r.__model__
        if T in r.__type_params__:
            return get_args(rT)[r.__type_params__.index(T)]
        return T  # type: ignore

    @classmethod
    def _openapi(
        cls,
        func: Callable,
        responses: dict[int, str | OpenAPIResponse],
    ) -> dict[int, OpenAPIResponse]:
        doc: dict[int, OpenAPIResponse] = {}
        models = signature(func).return_annotation
        for rT in cls._unpack(models):
            doc[rT.status_code.value] = rT._openapi(cls._body(rT))
        for code, desc in responses.items():
            if isinstance(desc, str):
                desc = doc.get(code, {}) | {"description": desc}
            doc[code] = desc
        return doc

    @classmethod
    def _annotate(cls, reqT: type[BaseModel] | type[None], respT: type[Response]):
        parameters = signature(reqT).parameters.values() if reqT is not NoneType else []
        annotations = get_type_hints(reqT, include_extras=True)
        bodies = set(cls._body(rT) for rT in cls._unpack(respT))
        sig = Signature(
            parameters=[
                param.replace(
                    default=missing
                    if param.default is not Parameter.empty
                    else Parameter.empty,
                    annotation=annotations[param.name],
                )
                for param in parameters
            ],
            return_annotation=BaseResponse[Union[*bodies]],
        )

        def decorator(wrapper: Callable) -> Callable:
            wrapper.__signature__ = sig  # type: ignore[attr-defined]
            wrapper.__annotations__ = annotations | {"return": sig.return_annotation}
            return wrapper

        return decorator

    def _expand(self, func: Callable) -> Callable:
        params = signature(func).parameters
        respT: type[Response] = signature(func).return_annotation
        match params.get("caller", None), params.get("request", None):
            case None, None:

                @self._annotate(NoneType, respT)
                def wrapper():
                    return func()

            case Parameter(), None:

                @self._annotate(NoneType, respT)
                def wrapper():
                    return func(caller=self.caller())

            case None, Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                @self._annotate(reqT, respT)
                def wrapper(**kwargs):
                    kwargs = {k: v for k, v in kwargs.items() if is_set(v)}
                    request = reqT.model_validate(kwargs)
                    return func(request=request)

            case Parameter(), Parameter() as reqP:
                reqT: type[BaseModel] = reqP.annotation

                @self._annotate(reqT, respT)
                def wrapper(**kwargs):
                    kwargs = {k: v for k, v in kwargs.items() if is_set(v)}
                    request = reqT.model_validate(kwargs)
                    return func(caller=self.caller(), request=request)

        return wrapper
