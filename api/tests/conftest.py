import json

import pytest


@pytest.fixture
def apigw_event():
    def _build(
        path: str,
        body: dict | None = None,
        method: str = "POST",
        headers: dict | None = None,
    ) -> dict:
        route_key = f"{method} {path}"

        event = {
            "version": "2.0",
            "routeKey": route_key,
            "rawPath": path,
            "rawQueryString": "",
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
