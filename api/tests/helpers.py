import json
from dataclasses import dataclass, field
from typing import Any

UNSET = object()
ADMIN_ID = "abc001"
USER_ID = "xyz001"


@dataclass
class ProviderMethod:
    result: Any = UNSET
    error: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        if self.result is UNSET:
            raise AssertionError("Provider result not configured")

        return self.result


def response_body(response: dict[str, Any]) -> dict[str, Any]:
    body = response.get("body")
    return json.loads(body) if body else {}


def assert_status(response: dict[str, Any], status: int) -> None:
    assert response["statusCode"] == status


def assert_body(response: dict[str, Any], expected: dict[str, Any]) -> None:
    assert response_body(response) == expected


def assert_no_body(response: dict[str, Any]) -> None:
    assert response.get("body") in (None, "")


def assert_problem(
    response: dict[str, Any],
    *,
    status: int,
    title: str,
    detail: str | None = None,
) -> None:
    assert_status(response, status)

    body = response_body(response)
    assert body["status"] == status
    assert body["title"] == title

    if detail is not None:
        assert body["detail"] == detail
