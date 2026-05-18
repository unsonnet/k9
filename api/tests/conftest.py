import json
from urllib.parse import urlencode

import pytest
from shared.abc import Caller, Role
from shared.providers.cognito import encode_id


@pytest.fixture
def current_caller():
    return {"claims": None}


@pytest.fixture
def apigw_event(current_caller):
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

        claims = current_caller["claims"]
        if claims is not None:
            event["requestContext"]["authorizer"] = {
                "jwt": {
                    "claims": claims,
                },
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
def caller_factory():
    def _build(
        *,
        id: str = "11111111-1111-1111-1111-111111111111",
        name: str = "Alice",
        role: Role = Role.USER,
    ) -> Caller:
        return Caller(
            id=id,
            name=name,
            role=role,
        )

    return _build


@pytest.fixture
def user_caller(caller_factory):
    return caller_factory(
        id="11111111-1111-1111-1111-111111111111",
        name="Alice",
        role=Role.USER,
    )


@pytest.fixture
def admin_caller(caller_factory):
    return caller_factory(
        id="22222222-2222-2222-2222-222222222222",
        name="Admin",
        role=Role.ADMIN,
    )


@pytest.fixture
def use_caller(current_caller):
    def _use(caller: Caller):
        current_caller["claims"] = {
            "cognito:username": encode_id(caller.id),
            "cognito:name": caller.name,
            "custom:role": caller.role.value,
        }
        return caller

    return _use


@pytest.fixture
def use_unauthorized_caller(current_caller):
    def _use():
        current_caller["claims"] = None

    return _use
