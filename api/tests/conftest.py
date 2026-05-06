import json
from urllib.parse import urlencode

import pytest
from shared.errors import DomainUnauthorized
from shared.http import Caller


@pytest.fixture
def apigw_event():
    def _build(
        path: str,
        body: dict | None = None,
        method: str = "POST",
        headers: dict | None = None,
        query_params: dict | None = None,
    ) -> dict:
        route_key = f"{method} {path}"

        clean_query_params = {
            key: value
            for key, value in (query_params or {}).items()
            if value is not None
        }
        raw_query_string = urlencode(clean_query_params)

        event = {
            "version": "2.0",
            "routeKey": route_key,
            "rawPath": path,
            "rawQueryString": raw_query_string,
            "headers": headers or {"content-type": "application/json"},
            "requestContext": {
                "accountId": "000000000000",
                "apiId": "api-id",
                "domainName": "localhost",
                "domainPrefix": "localhost",
                "http": {
                    "method": method,
                    "path": path,
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "pytest",
                },
                "requestId": "request-id",
                "routeKey": route_key,
                "stage": "$default",
                "time": "01/Jan/2026:00:00:00 +0000",
                "timeEpoch": 0,
            },
            "isBase64Encoded": False,
        }

        if clean_query_params:
            event["queryStringParameters"] = {
                key: str(value) for key, value in clean_query_params.items()
            }

        if body is not None:
            event["body"] = json.dumps(body)

        return event

    return _build


@pytest.fixture
def lambda_context():
    class Context:
        function_name = "k9-api"
        aws_request_id = "req-id"

    return Context()


@pytest.fixture
def response_body():
    def _parse(response: dict) -> dict:
        body = response.get("body")
        return json.loads(body) if body else {}

    return _parse


@pytest.fixture
def caller_factory():

    def _build(
        *,
        id: str = "user-1",
        name: str = "Alice",
        email: str | None = None,
        groups: tuple[str, ...] = (),
    ) -> Caller:
        return Caller(
            id=id,
            name=name,
            email=email or f"{id}@example.com",
            groups=groups,
        )

    return _build


@pytest.fixture
def user_caller(caller_factory):
    return caller_factory(
        id="user-1",
        name="Alice",
        email="alice@example.com",
        groups=("user",),
    )


@pytest.fixture
def admin_caller(caller_factory):
    return caller_factory(
        id="admin-1",
        name="Admin",
        email="admin@example.com",
        groups=("admin",),
    )


@pytest.fixture
def use_caller(monkeypatch: pytest.MonkeyPatch):
    def _use(handler_module, caller):
        monkeypatch.setattr(handler_module.app, "caller", lambda: caller)
        return caller

    return _use


@pytest.fixture
def use_unauthorized_caller(monkeypatch: pytest.MonkeyPatch):
    def _use(handler_module):
        def _raise():
            raise DomainUnauthorized()

        monkeypatch.setattr(handler_module.app, "caller", _raise)

    return _use
