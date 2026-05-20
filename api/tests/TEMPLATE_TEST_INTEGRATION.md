# Integration Test Handoff: `test_integration.py` for API Endpoint Services

## Purpose

Use this document as the implementation template for creating a service-level `test_integration.py` for an API endpoint service when given:

- `handler.py`
- `payloads.py`
- `service.py`
- one or more provider protocol modules
- the existing `tests/conftest.py`
- the existing `tests/helpers.py`

The output is a concise, standardized, endpoint-oriented integration test suite. It must exercise the public Lambda/API boundary by invoking `lambda_handler` with API Gateway-shaped events. It must not call service methods directly.

The suite should read as the API contract for the service: routes, request validation, authentication/authorization behavior, response serialization, provider calls, domain-error mapping, and basic routing behavior.

Do not maximize line coverage by producing many tiny or speculative tests. Cover the behavior that is visible at the HTTP boundary and important to the endpoint contract.

---

## Required first step: derive an endpoint inventory

Before writing code, derive an endpoint inventory from `handler.py`, `payloads.py`, `service.py`, and provider protocols. Use it to drive the file. The inventory does not need to be printed in the final test file, but the generated tests must follow it exactly.

For each endpoint, identify:

| Field | What to derive |
|---|---|
| Method | HTTP method registered by the handler. |
| Path | Exact route path, using `{param}` notation for path variables. |
| Operation name | Canonical name used for the test class. |
| Success status | Expected status code. |
| Response body | Serialized JSON body, or no body for `204`. |
| Request body | Required/optional fields, aliases, validators, enum values, normalization. |
| Query params | Supported params, defaults, parsing, validation, normalization. |
| Path params | Validation rules and aliases such as `me`. |
| Auth rule | Public, authenticated, admin-only, self-or-admin, admin-field-only, etc. |
| Provider method | Exact provider protocol method called on success. |
| Provider arguments | Exact normalized arguments passed to the provider. |
| Domain errors | Domain exceptions caught by the handler and their status/title/detail mapping. |
| Unsupported method case | One unsupported method/path pair for routing tests. |
| Representative success input | Ordinary valid body/query/path values that prove the normal contract without mixing in edge-case normalization. |
| Representative validation cases | Required-field, enum, blank-string, scalar, and cross-field cases explicitly supported by payload validators. |

Write tests in handler route order unless there is an obvious public API ordering already established by the route declarations.

---

## Required top-level file shape

Use this top-level structure:

```python
import importlib
from collections.abc import Callable
from datetime import datetime, timezone  # only when needed
from typing import Any

import pytest
# application imports
# test helper imports

pytestmark = pytest.mark.integration


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

# constants, shared error parameter sets, fake providers, small factories


# ──── Fixtures ────────────────────────────────────────────────────────────────────────

# provider fixtures, handler reload fixture, invoke fixture, provider return fixtures


# ──── METHOD /route ───────────────────────────────────────────────────────────────────

class TestOperationName:
    ...


# ──── Routing ─────────────────────────────────────────────────────────────────────────

class TestRouting:
    ...
```

Rules:

- Use the Unicode section comments shown above.
- Use one blank line after each section header and two blank lines before each class/function as Black would produce.
- Do not add explanatory comments inside tests unless they clarify a non-obvious domain constraint.
- Keep service-specific setup local to `test_integration.py`.

---

## Imports and typing standards

Use this import order:

1. standard library
2. third-party packages
3. application/domain imports
4. `tests.helpers` imports

Rules:

- Import `importlib` when the handler is reloaded after monkeypatching provider constructors.
- Import `Callable` from `collections.abc` for invoke fixtures.
- Import `Any` only when used for JSON dictionaries or flexible invoke signatures.
- Import `datetime, timezone` only when the service serializes or parses datetimes.
- Import provider model classes used for fake return values.
- Do not alias provider model imports unless two imported symbols have the exact same name. Never add `Provider` prefixes merely to distinguish provider models from fixtures or response helpers.
- Import domain errors that are asserted in provider-error tests.
- Import caller/auth types only when the test signatures use them.
- Prefer a single-line `from tests.helpers import ...` when it fits Black's line length; otherwise let Black wrap it.
- Do not import concrete provider classes directly when monkeypatching provider modules is cleaner.
- Do not import unused helpers such as `assert_no_body` unless the file has a `204` test.

---

## Helper-section ordering

The `Helpers` section should be deterministic:

1. deterministic constants
2. shared domain-error parameter sets
3. fake provider classes
4. provider model factories
5. expected API body factories

If there are no constants, begin with the first needed helper category. Keep each category compact.

### Constants

Use stable values with domain-specific names. Prefer the route/entity name over generic names.

```python
TEST_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
UTC = timezone.utc
USER_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_ID = "22222222-2222-2222-2222-222222222222"
OTHER_USER_ID = "33333333-3333-3333-3333-333333333333"
REPORT_ID = "report-1"
```

Rules:

- Use constants for repeated resource IDs, role-specific caller IDs, timestamps, and shared cursors.
- Name ID constants after the domain entity: `USER_ID`, `ORG_ID`, `REPORT_ID`, `OTHER_USER_ID`. Use `RESOURCE_ID` only when the service has no clear domain noun.
- Do not replace meaningful service-specific constant names with generic names.
- Do not create constants for simple token/session/password strings by default; prefer local literals or fixture defaults unless the same value is reused across many route families or its identity is semantically important.
- Keep canonical display values distinct from normalized provider values when normalization is part of the contract. Example: API response name `"Alice"` and provider argument `"alice"`.
- Prefer simple valid sample values already present or implied in the service/payload code. Do not invent stronger, more complex, whitespace-heavy, or quote-heavy values than necessary.
- Use whitespace, quote escaping, case folding, and other normalization-specific sample values only in a dedicated normalization test, not in the ordinary success test.

### Domain-error parameter sets

Define reusable error parameter sets only when multiple endpoints share identical mappings.

```python
PROVIDER_ERRORS = [
    pytest.param(DomainUnauthorized(), 401, "Unauthorized", id="unauthorized"),
    pytest.param(DomainForbidden(), 403, "Forbidden", id="forbidden"),
    pytest.param(DomainRateLimited(), 429, "Too Many Requests", id="rate-limited"),
]

PROVIDER_ERRORS_WITH_NOT_FOUND = [
    PROVIDER_ERRORS[0],
    PROVIDER_ERRORS[1],
    pytest.param(DomainNotFound(), 404, "Not Found", id="not-found"),
    PROVIDER_ERRORS[2],
]
```

For endpoints with custom problem details, use endpoint-specific sets:

```python
ACTION_ERRORS = [
    pytest.param(
        DomainInvalidCredentials(),
        401,
        "Unauthorized",
        "Invalid credentials",
        id="invalid-credentials",
    ),
    pytest.param(
        DomainUnauthorized(),
        401,
        "Unauthorized",
        "Invalid credentials",
        id="unauthorized",
    ),
    *COMMON_ACTION_ERRORS,
]
```

Rules:

- Use `pytest.param(..., id="...")` for every case.
- Keep IDs short, kebab-case, and semantic.
- Include `detail` in the tuple only when the handler supplies custom detail.
- Do not reuse a shared set if status, title, or detail differs.
- Inspect each endpoint's handler `except` clauses and service/provider error surface. Include every domain exception that the endpoint intentionally maps, even when multiple exceptions map to the same status/title/detail.
- For endpoint-specific authentication or credential failures, keep the endpoint-specific detail text in the error set; do not collapse those cases into a generic shared auth error set.
- Include a `500 Internal Server Error` test when the handler has a documented or visible fallback for otherwise-unexpected domain errors.

### Fake provider classes

Use local fake classes with `ProviderMethod`.

```python
class FakeExampleProvider:
    def __init__(self) -> None:
        self.list_items = ProviderMethod()
        self.create_item = ProviderMethod()
        self.delete_item = ProviderMethod(result=None)
```

Rules:

- The fake should contain only provider methods called by this service.
- Use the exact provider protocol method names.
- Use `ProviderMethod(result=None)` for successful provider methods that return `None`.
- Do not use `Mock`, `MagicMock`, or broad fake methods.
- Assert calls with exact dictionaries in call order for success and authorization-derived behavior.

### Provider model and response body factories

Use small local factories only when they remove meaningful repetition or clarify serialization.

```python
def make_item(
    *,
    id: str = RESOURCE_ID,
    name: str = "Alice",
    enabled: bool = True,
) -> Item:
    return Item(
        id=id,
        name=name,
        enabled=enabled,
        created_at=TEST_NOW,
        updated_at=None,
    )


def item_body(
    *,
    id: str = RESOURCE_ID,
    name: str = "Alice",
    enabled: bool = True,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "enabled": enabled,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": None,
    }
```

Rules:

- Use provider model types for fake provider return values.
- Use JSON-shaped dictionaries for expected API response bodies.
- Body helpers must use API field names exactly, including camelCase.
- Use `make_<model>` for provider model construction when overrides are useful.
- Use `<resource>_body` for expected API JSON.
- Do not create `make_` helpers for simple records used only once; prefer a fixture or inline construction.
- Do not create `make_<page>` helpers unless the same page shape is constructed in multiple tests with meaningful variants. A page fixture may construct the page object directly.
- Do not create credential/token helpers unless the object is built repeatedly with variants. A single `<resource>_creds` or `<resource>_tokens` fixture may inline the model construction.
- Do not create broad builders with many flags.
- Do not create helpers that only hide one or two literal lines unless the name carries semantic meaning.
- Match provider model construction to the actual provider model. If the provider model requires encoded IDs, aliases, or `model_validate`, use that exact shape rather than a generic constructor pattern.

---

## Fixture standards

Use fixtures for canonical provider instances, reloaded handler module, invoke helper, and canonical provider return records.

### Provider fixtures

```python
@pytest.fixture
def example_provider() -> FakeExampleProvider:
    return FakeExampleProvider()
```

### Handler reload fixture

Handler modules often construct services/providers at import time. Monkeypatch concrete provider constructors before reloading the handler module.

```python
@pytest.fixture
def example_handler_module(
    monkeypatch: pytest.MonkeyPatch,
    example_provider: FakeExampleProvider,
):
    import example.provider as example_provider_module

    monkeypatch.setattr(
        example_provider_module,
        "ConcreteExampleProvider",
        lambda: example_provider,
    )

    import example.handler as handler

    return importlib.reload(handler)
```

Rules:

- Patch the constructor name that `handler.py` uses indirectly through the provider module.
- Patch every provider used by the service before importing/reloading the handler.
- Keep handler reload fixtures service-specific and local.
- Do not move provider fakes or handler reload logic to `conftest.py`.

### Invoke fixture

Use one service-level invoke fixture. Do not create one invoke helper per endpoint.

For body-only `POST` action services:

```python
@pytest.fixture
def invoke_service_api(
    service_handler_module,
    apigw_event,
    lambda_context,
) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    def invoke(path: str, body: dict[str, Any]) -> dict[str, Any]:
        return service_handler_module.lambda_handler(
            apigw_event(path, body),
            lambda_context,
        )

    return invoke
```

For mixed-method services:

```python
@pytest.fixture
def invoke_service_api(
    service_handler_module,
    apigw_event,
    lambda_context,
) -> Callable[..., dict[str, Any]]:
    def invoke(
        path: str,
        *,
        method: str = "GET",
        body: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return service_handler_module.lambda_handler(
            apigw_event(
                path,
                body,
                method=method,
                query_params=query_params,
            ),
            lambda_context,
        )

    return invoke
```

Rules:

- For mostly `POST` body endpoints where the default event method is already correct, keep the invoke signature small.
- For mixed-route services, make `method`, `body`, and `query_params` keyword-only.
- Use the raw handler module directly in routing tests.

### Provider return fixtures

Use fixtures for canonical provider return records that appear in multiple tests.

```python
@pytest.fixture
def item_record() -> Item:
    return make_item()


@pytest.fixture
def item_page(
    item_record: Item,
) -> ItemPage:
    return ItemPage(
        items=[item_record],
        cursor="next-cursor",
    )
```

Rules:

- Use `<resource>_record` for canonical single model instances.
- Use `<resource>_page` for canonical page objects.
- Use `<resource>_creds`, `<resource>_tokens`, or similarly semantic fixture names when the provider model is not a normal record.
- Prefer fixtures for repeated success return objects instead of repeatedly inlining model construction.
- Inline a page object only when it is used once and no canonical page fixture is useful.

---

## Endpoint class naming

Every route or tightly coupled route family gets one class.

Derive class names mechanically:

| Route shape | Class name |
|---|---|
| `GET /resources` | `TestListResources` |
| `POST /resources` | `TestCreateResource` |
| `GET /resources/{resourceId}` | `TestGetResource` |
| `PATCH /resources/{resourceId}` | `TestUpdateResource` |
| `PUT /resources/{resourceId}` | `TestReplaceResource` |
| `DELETE /resources/{resourceId}` | `TestDeleteResource` |
| `POST /resources/{resourceId}/action` | `TestActionResource` |
| `GET /resources/{resourceId}/children` | `TestListChildren` |
| `POST /service/action` | `TestAction` |

Rules:

- Use domain words from the route and handler operation, not provider method names, when they differ.
- Singularize the resource for item operations.
- Use plural for collection list classes.
- For action endpoints, prefer the action verb/noun from the path: `TestLogin`, `TestRefresh`, `TestResetResource`, `TestExportReport`.
- If one path supports multiple methods, create one class per method unless the handler treats them as one inseparable operation.

Each class must be preceded by the exact route section header:

```python
# ──── GET /resources/{resourceId} ─────────────────────────────────────────────────────


class TestGetResource:
    ...
```

---

## Endpoint test ordering

Inside each endpoint class, use this order:

1. primary success path
2. tightly related success variants that exercise a distinct response/control-flow branch
3. narrowly targeted normalization or caller-claim parsing tests, only when warranted
4. provider/domain error mapping for public action endpoints with no auth branches
5. validation of invalid body/query/path
6. authentication required
7. authorization forbidden
8. provider/domain error mapping for authenticated/authorized endpoints

This order is mandatory unless the existing service test suite has a clearer local convention. Public action endpoints should place `test_maps_provider_errors` after success/normalization tests and before invalid-body tests. Authenticated resource endpoints should place validation before auth/authz and provider-error tests.

Do not scatter tests of the same concern across the class. Do not insert extra “confidence” tests that are merely plausible; every test must correspond to an explicit route branch, payload validator, service authorization branch, response branch, or provider-error mapping.

---

## Standard test method names

Use these names unless the endpoint needs a more specific domain phrase.

### Success names

| Situation | Test name |
|---|---|
| Collection response | `test_returns_page` |
| Created resource | `test_returns_created_<resource>` |
| Read resource | `test_returns_<resource>` |
| Updated resource | `test_returns_updated_<resource>` |
| Deleted/no-content response | `test_returns_no_content` |
| Action returns credentials | `test_returns_reset_<resource>_credentials` or domain equivalent |
| Action returns tokens | `test_returns_tokens` |
| Action returns challenge/follow-up | `test_returns_challenge`, `test_returns_followup_challenge` |
| Action accepts alternative input | `test_accepts_<alternative>` |

Rules:

- Keep success names generic and stable. Do not encode every field into the name.
- Use `test_returns_page` for paginated collection endpoints; avoid `test_returns_<resources>_page` unless there are multiple page shapes in one class.
- For multiple success variants that differ only by caller/path/body arguments while using the same provider method, status, and response shape, prefer one parametrized success test with explicit expected provider calls.
- Use separate success test methods only for semantically distinct response/control-flow branches, such as tokens versus challenge, no-content versus body, or a genuinely different provider method.
- Do not add a success test for every enum value, optional field, or role unless that value changes authorization, provider arguments in a meaningful branch, or response shape.
- For challenge-like flows, pair each request challenge with a realistic response shape from the protocol. Use `test_returns_tokens` for the terminal success and `test_returns_followup_challenge` when responding to one challenge yields another challenge.

### Normalization names

Use these names when testing normalization separately from the primary success case:

- `test_passes_normalized_query_to_provider`
- `test_passes_normalized_body_to_provider`
- `test_passes_normalized_path_params_to_provider`
- `test_accepts_comma_delimited_groups_claim`

Only add a normalization test when all of these are true:

- the behavior is explicitly implemented in `payloads.py` or `service.py`
- it is not already shown by the primary success test
- it is semantically important at the API boundary

Do not add separate body-normalization tests for ordinary create/login/challenge bodies when the success test already asserts the normalized provider call or when the normal contract does not require edge-case whitespace/case input. Query-string normalization, quote escaping, and caller-claim parsing are better candidates for separate tests than routine body lowercasing.

### Validation names

| Validation type | Test name |
|---|---|
| Body | `test_rejects_invalid_body` |
| Query params | `test_rejects_invalid_query_params` |
| Path ID | `test_rejects_invalid_<param_name>` |
| Mutually exclusive fields | Prefer a specific name such as `test_rejects_both_<fields>` when the exactly-one/at-least-one rule is central to the endpoint; otherwise use `test_rejects_invalid_body`. |

Rules:

- Parametrize invalid body/query tests when the cases share the same assertion. Use a single explicit test when the invalid case is a named domain constraint.
- For validation tests, normally assert only `assert_status(response, 422)`. Do not use `assert_problem` for validation unless the service already documents validation problem bodies as part of the public contract.
- For body/query validation, do not include a provider fixture solely to assert no calls.
- For path validation, prefer `assert_status(response, 422)` as well. Assert provider calls are empty only when the provider fixture is already natural for the test or the suite consistently checks that boundary for path parsing.
- Do not assert full validation bodies unless they are a documented API contract.

### Auth/authz names

Use these names consistently:

- `test_requires_authentication`
- `test_requires_admin`
- `test_forbids_user_reading_other_user`
- `test_forbids_user_updating_other_user`
- `test_forbids_user_updating_admin_only_fields`
- `test_forbids_user_reading_other_users_<children>`

Rules:

- Use `assert_problem(..., status=401, title="Unauthorized")` for missing/invalid caller.
- Use `assert_problem(..., status=403, title="Forbidden")` for forbidden role/scope.
- Always assert the relevant provider method was not called when auth/authz blocks before provider access.

### Provider error names

Use:

- `test_maps_provider_errors`
- `test_is_idempotent`
- `test_maps_unexpected_domain_error`

Rules:

- Use `test_maps_provider_errors` for regular domain exception mapping.
- Use a specific name for intentional special cases, such as idempotent logout/revoke behavior.
- Use valid request input so the provider is reached.

---

## Success-path standards

A success test should follow arrange/act/assert:

```python
def test_returns_created_item(
    self,
    item_provider: FakeItemProvider,
    invoke_service_api,
    admin_caller: Caller,
    use_caller,
    item_record: Item,
) -> None:
    use_caller(admin_caller)
    item_provider.create_item.result = item_record

    response = invoke_service_api(
        "/items",
        method="POST",
        body={
            "name": "Alice",
            "role": "user",
        },
    )

    assert_status(response, 201)
    assert_body(response, item_body())
    assert item_provider.create_item.calls == [
        {
            "name": "alice",
            "role": Item.Role.USER,
        }
    ]
```

Rules:

- Arrange caller and provider result/error first.
- Act once.
- Assert status before body.
- Assert exact provider calls for success paths.
- Assert normalized provider arguments, not raw request values, when payload/service normalizes input.
- The primary success test should use ordinary valid inputs. Do not combine primary success with edge-case normalization samples unless the endpoint has no other way to show its core behavior.
- For collection/list endpoints with supported query parameters, the primary success test must pass a representative full query and assert every provider argument, including defaults only where intentionally omitted. Include parsed datetimes, booleans, limits, and cursors when those query fields exist.
- Use a separate normalization test only for behavior such as trimming, quote escaping, case folding, or caller-claim parsing that is not already covered by the primary success test.
- When parametrizing self/admin/path aliases, keep the provider return fixture canonical unless the response body itself is supposed to vary by caller/path. The parameterization should primarily vary the request path/caller and expected provider call, not invent different return records.
- For `204`, assert `assert_status(response, 204)` and `assert_no_body(response)`.
- Keep request bodies explicit dictionaries in the test.
- Prefer canonical fixtures for provider return records/pages.

---

## Parametrization standards

Use `pytest.mark.parametrize` when multiple cases have the same shape and the same assertions.

Rules:

- Every case must use `pytest.param(..., id="kebab-case")`.
- Parameter names should be semantic: `body`, `query_params`, `provider_error`, `expected_status`, `expected_title`, `expected_detail`.
- For access variants with identical behavior, parametrize over `caller_fixture`, `path`, and expected provider arguments.
- For update endpoints where caller/path/body variants change provider arguments, parametrize over `caller_fixture`, `path`, `body`, and `expected_provider_call` rather than creating separate tests for each variant.
- Use `request.getfixturevalue(caller_fixture)` only for parametrized caller fixture selection.
- Do not split identical self/admin success variants into separate tests if a compact parametrized test is clearer.
- Do not parametrize unrelated behavior just to reduce line count.

Example for self/admin alias variants:

```python
@pytest.mark.parametrize(
    ("caller_fixture", "path", "expected_provider_id"),
    [
        pytest.param("user_caller", "/resources/me", RESOURCE_ID, id="self-alias"),
        pytest.param("user_caller", f"/resources/{RESOURCE_ID}", RESOURCE_ID, id="self-id"),
        pytest.param("admin_caller", f"/resources/{RESOURCE_ID}", RESOURCE_ID, id="admin-other"),
        pytest.param("admin_caller", "/resources/me", ADMIN_ID, id="admin-self-alias"),
    ],
)
def test_returns_resource(
    self,
    request,
    resource_provider: FakeResourceProvider,
    invoke_service_api,
    use_caller,
    resource_record: Resource,
    caller_fixture: str,
    path: str,
    expected_provider_id: str,
) -> None:
    caller = request.getfixturevalue(caller_fixture)
    use_caller(caller)
    resource_provider.get_resource.result = resource_record

    response = invoke_service_api(path)

    assert_status(response, 200)
    assert_body(response, resource_body())
    assert resource_provider.get_resource.calls == [{"id": expected_provider_id}]
```

---

## Validation standards

Derive invalid cases from `payloads.py`. Do not invent cases unsupported by the validators.

Body validation should usually include only cases directly implied by `payloads.py`:

- missing all required fields, with ID `missing-all-fields`, when it adds information beyond per-field missing cases
- each missing required field, with IDs like `missing-name` and `missing-role`, when useful
- blank string for required strings, with IDs like `blank-name`
- invalid enum values, using an invalid value close to the domain such as `"owner"` for a role field rather than an unrelated value
- invalid scalar type values only when the payload model has meaningful scalar coercion/strictness behavior worth documenting
- mutually exclusive or at-least-one constraints
- cross-field validators, such as invalid date ranges

Query validation should usually include:

- invalid boolean strings
- invalid datetime strings
- invalid limit bounds if bounds exist, with IDs such as `limit-too-small` and `limit-too-large`
- invalid cursor/token shape only if the payload validates it
- invalid cross-field relationships, with domain wording such as `backwards-date-range` when applicable

Rules:

- Keep invalid cases representative and minimal.
- Prefer required-field, blank-string, enum, and explicit cross-field cases over speculative strength/format cases.
- For strings such as passwords, tokens, sessions, codes, and cursors, test missing/blank only unless `payloads.py` explicitly validates length, regex, type strictness, or strength. Do not invent invalid token formats, short sessions, password-strength failures, or numeric-token cases.
- For nested bodies, test missing top-level required fields first. Do not invent nested response cases unless `payloads.py` explicitly validates that nested shape.
- Use valid authentication for validation tests on authenticated endpoints so auth does not mask validation.
- Do not include provider fixtures solely to assert calls are empty in body/query validation tests.
- If several endpoints share the same path parameter validator, test invalid path parameters sparingly. Do not duplicate invalid UUID/path tests in every endpoint class. Prefer one representative route or only endpoints with a unique path constraint, such as an action route that does not accept a common alias.
- For common aliases such as `/me`, test the alias where it is accepted. Test rejection of the alias only on routes where `handler.py` or `payloads.py` explicitly disallows it and that rule is part of the endpoint contract.

---

## Authentication and authorization standards

Use shared caller fixtures from `conftest.py` when available:

- `user_caller`
- `admin_caller`
- `use_caller`
- `use_unauthorized_caller`

Rules:

- Public endpoints should not receive auth tests.
- Authenticated endpoints need `test_requires_authentication` unless an endpoint family already covers an identical route-level requirement and duplicating it would be noise.
- Admin-only endpoints need `test_requires_admin`.
- Self-or-admin endpoints should test:
  - self alias, when supported
  - self ID, when supported
  - admin reading/updating another user/resource
  - non-admin blocked from another user/resource
- For self-or-admin success parametrization, use all supported self/admin aliases. Do not substitute an admin-other case with a user-other forbidden case; the latter belongs in the explicit forbidden test.
- Admin-field-only endpoints should test the non-admin block compactly. Parametrize over the admin-only field bodies when they share the same assertion. Do not add separate success tests for each admin-only field unless the allowed admin path has a distinct provider/result branch; otherwise include the admin-only body as a case in the primary update-success parametrization.
- If shared auth parsing supports both list and comma-delimited group claims, include one targeted test for role parsing in the most representative admin-gated endpoint.
- Always assert provider calls remain empty when the handler/service blocks before provider access.

---

## Provider error mapping standards

Use provider `.error` to simulate domain failures.

```python
@pytest.mark.parametrize(
    ("provider_error", "expected_status", "expected_title"),
    PROVIDER_ERRORS_WITH_NOT_FOUND,
)
def test_maps_provider_errors(
    self,
    item_provider: FakeItemProvider,
    invoke_service_api,
    admin_caller: Caller,
    use_caller,
    provider_error: Exception,
    expected_status: int,
    expected_title: str,
) -> None:
    use_caller(admin_caller)
    item_provider.get_item.error = provider_error

    response = invoke_service_api(f"/items/{RESOURCE_ID}")

    assert_problem(
        response,
        status=expected_status,
        title=expected_title,
    )
```

Rules:

- Use a valid request.
- Configure the exact provider method used by the endpoint.
- Assert `detail` only when the handler sets custom detail.
- For endpoint-specific details, use endpoint-specific error parameter sets.
- For idempotent operations, test intentionally swallowed provider errors separately from ordinary provider-error mapping. Parametrize all swallowed errors only when `service.py` or `handler.py` explicitly swallows each one; do not infer additional idempotent errors from similar status codes.
- Add `test_maps_unexpected_domain_error` only when the endpoint has an explicit broad domain-error fallback or documented fallback behavior that is not already covered by the normal provider-error set. Do not add this test to every endpoint.
- Do not remove a route-specific fallback test just because the same status appears in a shared error set.
- Do not assert provider calls after a provider error unless the call assertion is part of a specific regression; the configured provider error already proves the provider was reached.
- Do not assert implementation internals, stack traces, or logs.

---

## Routing test standards

Every integration file should end with a `TestRouting` class unless routing is tested elsewhere for the same handler.

Unsupported methods:

```python
@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("PATCH", "/resources", id="list-create-resource"),
        pytest.param("POST", "/resources/me", id="get-resource"),
        pytest.param("GET", f"/resources/{RESOURCE_ID}/action", id="action-resource"),
    ],
)
def test_rejects_unsupported_methods(
    self,
    service_handler_module,
    apigw_event,
    lambda_context,
    method: str,
    path: str,
) -> None:
    response = service_handler_module.lambda_handler(
        apigw_event(path, {}, method=method),
        lambda_context,
    )

    assert_status(response, 405)
```

Unknown route:

```python
def test_returns_not_found_for_unknown_route(
    self,
    service_handler_module,
    apigw_event,
    lambda_context,
) -> None:
    response = service_handler_module.lambda_handler(
        apigw_event("/resources/unknown/path", {}, method="GET"),
        lambda_context,
    )

    assert_status(response, 404)
```

Rules:

- Use one unsupported method/path case per route family or per registered route shape, following the existing suite's compactness. Do not add extra unsupported-method cases merely because more paths exist.
- Use a method that is clearly unsupported for that path and mirrors the endpoint family being tested.
- If all unsupported-method cases in a file use the same method, parametrize only `path` and hardcode the method in the call. If methods differ, parametrize `("method", "path")`.
- For action-only `POST` endpoints, `GET` to the same path is a good unsupported-method case.
- For collection paths supporting `GET` and `POST`, choose a third method such as `PATCH` or `DELETE`.
- For item paths supporting `GET` and `PATCH`, choose `POST` or `DELETE`.
- For unknown routes, use the service prefix with a short path that cannot match any registered route, such as `/service/unknown` or `/service/me/unknown`. Avoid deeply nested unknown paths unless needed to avoid matching a dynamic route.
- Assert status only unless the routing problem body is a documented contract.

---

## Shared `conftest.py` guidance

Use existing shared fixtures when possible. Propose edits to `conftest.py` only when the need is generic and likely to recur across services.

Appropriate generic additions:

- optional `headers` support in `apigw_event`
- optional `query_params` support in `apigw_event`
- common API Gateway path/method/body structure
- common Lambda context
- common caller fixtures
- common utilities for auth claims or group formatting

Do not move these into `conftest.py`:

- service-specific provider fakes
- service-specific handler reload fixtures
- service-specific invoke fixtures
- service-specific model factories
- service-specific IDs, tokens, pages, or payloads
- endpoint-specific invalid payload lists

If a generic event capability is missing, propose the smallest additive change. Do not invent service-specific wrappers.

---

## Shared `helpers.py` guidance

The shared helper layer should remain small.

Expected generic helpers include:

- `ProviderMethod`
- `response_body`
- `assert_status`
- `assert_body`
- `assert_no_body`
- `assert_problem`

Propose edits to `helpers.py` only for helpers that are:

1. generic across services
2. repetitive
3. semantically meaningful
4. clearer than inline assertions

Appropriate helper candidates:

- a small assertion for a standard problem response if `assert_problem` becomes insufficient
- a tiny extension to `ProviderMethod` needed by several services
- a standard pagination assertion only if many services share the exact same page envelope

Inappropriate helper candidates:

- provider fakes
- body factories
- model factories
- endpoint-specific invalid payload lists
- service-specific request builders
- wrappers that hide route, method, or expected provider call
- helpers that save one or two lines but obscure the API contract

Prefer inline code for one-off values. Prefer local helpers for repeated service-specific construction. Prefer shared helpers only for cross-service testing primitives.

---

## Programming style requirements

Follow these rules consistently:

- Keep tests concise, explicit, and organized.
- Use one arrange/act/assert flow per test.
- Avoid clever abstractions.
- Avoid inheritance and shared mutable state in test classes.
- Avoid loops inside tests when parametrization is clearer.
- Avoid broad helper functions that take many flags.
- Avoid snapshots.
- Use deterministic fixtures and constants.
- Use exact dictionaries for expected bodies and provider calls.
- Keep expected response bodies close to the endpoint contract.
- Use keyword arguments for body/model helpers when it improves readability.
- Keep request dictionaries explicit in tests.
- Keep comments limited to section headers and rare non-obvious cases.
- Do not add hundreds of helpers. Add helpers only where they remove repeated, semantically meaningful code.

The generated file should be minimal but not under-specified. A reader should be able to understand the route contract without opening the implementation.

---

## How to derive the suite from the supplementary files

Inspect in this order:

1. `handler.py`
   - route methods and paths
   - success status codes
   - response serialization
   - error mappings
   - provider constructors created at import time
   - caller/auth extraction

2. `payloads.py`
   - required body/query/path fields
   - aliases and casing
   - enum values
   - validators
   - normalization
   - date/boolean/limit parsing
   - cross-field validation

3. provider protocol modules
   - protocol method names
   - return model classes
   - argument names and types
   - enum/data model types used in exact provider-call assertions

4. `service.py`
   - normalization before provider calls
   - caller-derived IDs
   - `me` alias behavior
   - role checks and admin-only fields
   - provider method selection
   - swallowed/idempotent domain errors

5. `conftest.py` and `helpers.py`
   - reusable API Gateway event fixtures
   - caller setup utilities
   - assertion helpers
   - generic capabilities that may need a small proposal or edit

Do not test private service internals directly. Test the observable API behavior through `lambda_handler`.

---

## Endpoint coverage checklist

For each endpoint, ensure the final test file covers the applicable items:

- section header with exact method/path
- standardized class name
- primary success response
- alternate success responses, if the endpoint has them
- exact response body or no body
- exact provider method called
- exact provider arguments after validation and normalization
- representative invalid body/query/path inputs
- authentication required, if applicable
- authorization rule, if applicable
- self/admin alias behavior, if applicable
- admin-only field behavior, if applicable
- provider domain error mapping
- idempotent/swallowed provider error behavior, if applicable
- one unsupported method case in `TestRouting`
- one unknown route case in `TestRouting`

---


## Done criteria

A completed `test_integration.py` should satisfy all of the following:

- Uses `pytestmark = pytest.mark.integration`.
- Uses fake provider classes with `ProviderMethod`.
- Monkeypatches concrete provider constructors before handler reload.
- Invokes `lambda_handler` through `apigw_event` and `lambda_context`.
- Groups tests by endpoint class with exact route section headers.
- Uses standardized class and test method names.
- Uses canonical provider return fixtures where repeated.
- Asserts success status and body for every route.
- Asserts exact provider calls for success and authorization-derived behavior.
- Covers representative invalid body/query/path requests with `422`.
- Covers auth/authz failures where applicable and verifies provider calls remain empty.
- Covers provider domain-error mappings.
- Covers unsupported methods and unknown routes.
- Uses helpers only where they reduce meaningful repetition.
- Keeps service-specific factories local.
- Does not introduce broad, opaque, or excessive helper abstractions.
- Reads as a concise API contract for the service.
