# Provider Test Handoff: `test_<provider>.py` for Service Provider Implementations

## Purpose

Use this document as the implementation template for creating provider-level test files for a service when given:

- `handler.py`
- `payloads.py`
- `service.py`
- one or more provider protocol/implementation modules
- the existing `tests/conftest.py`
- the existing `tests/helpers.py`

The output is one concise, standardized `test_<provider>.py` file for each concrete provider implementation in the service. These are provider unit tests. They test concrete provider methods directly and assert the contract between the provider protocol and the external backing system or client.

The tests must not call `lambda_handler`, handler routes, payload request models, or service methods. Handler, payload, and service files are context for understanding the domain and intended provider behavior, but the subject under test is the concrete provider implementation.

The suite should read as the provider contract for the service: provider method inputs, external client calls, request payload construction, encoding/decoding, normalization internal to the provider, returned provider models, response parsing, branching behavior, default/clamped values, error translation, and invalid upstream response handling.

Do not maximize line coverage by producing many tiny or speculative tests. Cover behavior that is visible at the provider method boundary and important to the provider protocol. The generated file must be concise, organized, standardized, and minimal. Use helpers only where they remove repeated, semantically meaningful provider/client shapes.

---

## Core principle

A provider test should answer this question:

> Given a call to a concrete provider method, does the provider send the exact expected request(s) to its backing client, parse the exact expected response into provider protocol models, and translate external failures into domain errors?

Provider tests should not duplicate endpoint validation, authentication, authorization, or HTTP serialization tests. Those belong to integration tests. Provider tests should cover provider-specific encoding, client payload construction, client-call sequencing, response parsing, and external-error mapping.

---

## Required first step: derive a provider inventory

Before writing code, derive a provider inventory from the provider module first, then use `service.py`, `payloads.py`, and `handler.py` only to clarify domain semantics and expected use.

For each concrete provider and each protocol method it implements, identify:

| Field | What to derive |
|---|---|
| Provider module | Module path and concrete provider class to test. |
| Protocol method | Exact method name, arguments, defaults, and return type. |
| External backing system | AWS service, OpenSearch client, HTTP client, database client, filesystem client, or other dependency. |
| Provider constructor | Required constructor arguments and environment/client setup needed to instantiate without real external calls. |
| External operation sequence | Exact client methods called by the provider method, in order. |
| External request payloads | Exact keyword arguments, nested payloads, encoded IDs/names, filters, pagination tokens, auth parameters, query bodies, or headers passed to each client call. |
| Defaults and bounds | Provider-level defaults, clamping, omitted values, cursor handling, timestamp formatting, and optional argument behavior. |
| Branching behavior | Alternate external call sequences or return shapes based on inputs or upstream responses. |
| Return model | Provider model returned on success. |
| Response parsing | Required upstream fields, optional upstream fields, date/time normalization, enum conversion, encoded field decoding, cursor creation, and invalid shape handling. |
| Domain errors | External/client errors mapped to shared/domain exceptions. |
| Swallowed/idempotent errors | Provider errors intentionally swallowed or treated as successful. |
| Invariant failures | Invalid input or invalid upstream response shapes that should raise provider/domain invariant errors. |
| Deterministic values | IDs, encoded IDs, names, timestamps, cursors, passwords/secrets, tokens, and external index/pool/client identifiers used in tests. |

Every test in the file must correspond to a row or branch in this inventory. Do not add tests for behavior that is merely plausible but not implemented or implied by the provider protocol and implementation.

---

## Required top-level file shape

Use this top-level structure:

```python
from datetime import datetime, timezone  # only when needed
from typing import Any  # only when needed

import boto3  # only when needed
import pytest
from botocore.stub import Stubber  # only when needed
# other third-party client exceptions/types

import service.providers.provider as provider_module
from service.providers.provider import ProviderModel, ProviderPage
from shared.errors import DomainForbidden, DomainInvariantViolation, DomainNotFound
# other application imports

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

# constants, shared error cases, external payload factories, upstream response factories,
# fake clients or provider construction helpers, expected provider model factories


# ──── Fixtures ────────────────────────────────────────────────────────────────────────

# environment/client fixtures, provider fixture, stubber/fake-client fixtures,
# canonical provider return model fixtures only when useful


# ──── provider_method() ───────────────────────────────────────────────────────────────

class TestProviderMethod:
    ...


# ──── Provider Responses ──────────────────────────────────────────────────────────────

class TestResponseParsing:
    ...
```

Rules:

- Use `pytestmark = pytest.mark.unit`.
- Use the Unicode section comments shown above.
- Use one provider method section per protocol method, in protocol declaration order unless the provider implementation has a clearer domain order.
- Add `Provider Responses` only when there are response parsing, unexpected shape, decoding, datetime normalization, cursor, or unsupported upstream-response tests that are not naturally scoped to a single method.
- Do not include an endpoint `Routing` section.
- Do not include integration-test fixtures such as handler reload or API Gateway invocation.
- Use one blank line after each section header and two blank lines before each class/function as Black would produce.
- Keep service-specific setup local to the provider test file unless it is a genuinely generic test primitive.

---

## Imports and typing standards

Use this import order:

1. standard library
2. third-party packages and third-party exceptions
3. provider module import
4. provider model imports from the same module
5. shared/domain imports
6. test helper imports, only if needed

Rules:

- Import the provider module itself when monkeypatching module-level dependencies, helper functions, client constructors, or constants.
- Import provider model classes used in assertions, such as records, pages, credentials, tokens, or challenge models.
- Import external SDK/client types only when used in fixtures or type hints.
- Import external SDK exceptions that are used in error-mapping tests.
- Import `Any` only when helper dictionaries or fake clients require it.
- Import `datetime`, `timezone`, and `timedelta` only when timestamps are constructed, compared, or normalized.
- Do not alias provider modules or provider models unless a real name collision exists.
- Do not import handler or service modules unless a provider implementation directly needs their constants, which should be rare.
- Do not import `ProviderMethod`, `assert_status`, `assert_body`, or HTTP helpers for provider tests unless the provider genuinely uses a local callable fake where `ProviderMethod` is the best fit.
- Avoid unused imports from copied examples.

---

## Helper-section ordering

The `Helpers` section should be deterministic:

1. deterministic constants
2. shared provider/client error parameter sets
3. external request payload factories
4. upstream response factories
5. provider model factories or expected model factories
6. small client fakes or provider construction helpers

If a category is not needed, omit it. Do not add placeholder sections.

### Constants

Use stable values with domain-specific names.

```python
REGION = "us-east-1"
USER_POOL_ID = "pool-id"
INDEX = "reports"
USER_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_ID = "22222222-2222-2222-2222-222222222222"
RESOURCE_ID = "resource-1"
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, tzinfo=timezone.utc)
```

Rules:

- Use constants for repeated external identifiers, domain IDs, encoded IDs, timestamps, index/table/pool names, client IDs, and shared cursors.
- Name ID constants after the domain entity: `USER_ID`, `REPORT_ID`, `ORG_ID`, `RESOURCE_ID` only when no clearer noun exists.
- Keep raw domain values and encoded provider values separate when encoding is part of the provider contract.
- Do not create constants for one-off literal tokens, passwords, sessions, or error strings unless they are reused or semantically important.
- Use ordinary valid sample values in primary success tests. Reserve edge-case whitespace, escaping, high limits, malformed cursors, and unsupported enum values for targeted tests.

### Shared provider/client error cases

Define reusable error parameter sets only when multiple provider methods share the same external-error-to-domain-error mapping.

```python
PROVIDER_ERROR_CASES = [
    pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
    pytest.param("NotAuthorizedException", DomainForbidden, id="not-authorized"),
    pytest.param("TooManyRequestsException", DomainRateLimited, id="too-many-requests"),
    pytest.param("LimitExceededException", DomainRateLimited, id="limit-exceeded"),
    pytest.param("ResourceNotFoundException", DomainNotFound, id="resource-not-found"),
]
```

For non-AWS clients, parameterize over exception instances:

```python
PROVIDER_ERROR_CASES = [
    pytest.param(AuthenticationException(401, "unauthenticated"), DomainForbidden, id="authentication"),
    pytest.param(ConnectionTimeout("timed out"), DomainRateLimited, id="timeout"),
    pytest.param(NotFoundError(404, "missing"), DomainNotFound, id="not-found"),
]
```

Rules:

- Use `pytest.param(..., id="...")` for every case.
- IDs must be short, kebab-case, and tied to the upstream error or domain condition.
- Do not reuse a shared set if one method maps a code differently or excludes a code.
- Include every upstream error explicitly mapped by the provider implementation.
- Do not invent external error codes not present in the provider's exception map or visible handling.
- Keep method-specific error sets local when the method has custom behavior.

### External request payload factories

Use helper factories for external-client payloads when the expected request is nested, repeated, or semantically meaningful.

```python
def user_params(xid: str = USER_XID) -> dict[str, str]:
    return {
        "UserPoolId": USER_POOL_ID,
        "Username": xid,
    }


def list_resources_body(
    *,
    q: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    return {
        "size": min(limit or 25, 100),
        "query": {...},
        **({"search_after": decode_cursor(cursor)} if cursor else {}),
    }
```

Rules:

- Name payload helpers after the external operation or semantic payload: `user_params`, `list_users_params`, `create_user_params`, `list_reports_body`.
- Helpers should return the exact external payload shape expected by the SDK/client.
- Use keyword-only arguments for optional variants.
- Encode IDs/names, escape strings, clamp limits, serialize datetimes, and omit optional fields exactly as the provider does.
- Do not create helpers that hide a simple one-line payload used once.
- Do not create broad request builders with many unrelated flags.
- Keep helper defaults aligned with the primary success case.

### Upstream response factories

Use response factories when upstream response shapes are repeated or noisy.

```python
def upstream_user(
    *,
    id: str = USER_ID,
    name: str = "Alice",
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
) -> dict[str, Any]:
    return {
        "Username": encode_id(id),
        "Enabled": enabled,
        "UserCreateDate": created_at,
        "UserLastModifiedDate": updated_at,
        "Attributes": [
            {"Name": "preferred_username", "Value": encode_name(name)},
            {"Name": "name", "Value": name},
        ],
    }
```

Rules:

- Factories must represent upstream/client response shapes, not API response bodies.
- Use provider/client field names exactly.
- Include required fields by default.
- Allow narrow overrides for fields used by multiple tests.
- For invalid response tests, start from a valid response factory and mutate one field only when that makes the invariant clear.

### Provider model factories

Use provider model factories only when expected models are repeated with meaningful variants.

```python
def expected_resource(
    *,
    id: str = RESOURCE_ID,
    name: str = "Alice",
    enabled: bool = True,
) -> Resource:
    return Resource(
        id=id,
        name=name,
        enabled=enabled,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
    )
```

Rules:

- Use provider model classes for expected results.
- Do not create expected-model helpers for one-off records.
- Prefer direct equality against provider models over decomposed field assertions when the provider model has stable equality.
- Use `.model_validate(...)` only when the provider model itself requires validation from encoded/upstream-style data.

### Fake clients and provider construction helpers

Use tiny fake clients when the backing client does not have a robust stubber or when the provider calls only a few methods.

```python
class FakeSearchClient:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        return self.response


class RaisingSearchClient:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def search(self, **_: Any) -> Mapping[str, Any]:
        raise self.error
```

Rules:

- Fakes should implement only the external client methods used by the provider under test.
- Fakes should record exact calls where no third-party stubber validates expected parameters.
- For SDKs with a mature stubber, prefer the stubber over hand-written fakes.
- Use a `make_provider(client)` helper when the provider is otherwise hard to construct without real network setup.
- Keep fakes local to the test file unless the same fake is a generic client test primitive across services.

---

## Fixture standards

Use fixtures for environment isolation, external clients/stubbers, provider instances, and canonical expected provider models only when repeated.

### Environment fixtures

Provider constructors sometimes initialize SDK clients. Prevent real credentials, metadata discovery, or network calls.

```python
@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
```

Rules:

- Use `autouse=True` only for environment required by every test in the file.
- Keep environment fixtures minimal and deterministic.
- Do not let tests use real credentials, real endpoints, real network calls, or real mutable external resources.

### Client and stubber fixtures

For AWS/botocore providers:

```python
@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name=REGION)


@pytest.fixture
def provider(
    monkeypatch: pytest.MonkeyPatch,
    cognito_client,
) -> provider_module.CognitoProvider:
    monkeypatch.setattr(
        provider_module.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )

    return provider_module.CognitoProvider(
        region=REGION,
        user_pool_id=USER_POOL_ID,
        client_id="client-id",
    )


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber
```

For clients without a third-party stubber, construct fakes inline in tests or use a fixture only if many tests share the same fake setup.

Rules:

- Name the concrete provider fixture `provider` unless the file tests multiple concrete providers.
- Name external stubbers after the tool (`stubber`) or client when there are multiple clients.
- Monkeypatch the exact constructor or module-level dependency used by the provider module.
- Do not use `Mock` or `MagicMock` where a stubber or tiny fake gives exact request assertions.
- Do not move provider-specific client setup to `conftest.py`.

### Canonical model fixtures

Use fixtures for expected provider return models that appear in multiple tests.

```python
@pytest.fixture
def resource_record() -> Resource:
    return expected_resource()
```

Rules:

- Use `<resource>_record`, `<resource>_page`, `<resource>_tokens`, `<resource>_challenge`, or `<resource>_creds` when the model is repeated.
- Inline expected models in the test when the shape is unique to that test.
- Do not create fixtures only to shorten a single assertion.

---

## Provider class and method-section naming

Every protocol method should have one test class unless several methods are inseparable because the implementation shares a single private parser. Use method names mechanically.

| Provider method | Section header | Class name |
|---|---|---|
| `list_users()` | `# ──── list_users() ────` | `TestListUsers` |
| `create_user()` | `# ──── create_user() ────` | `TestCreateUser` |
| `get_user()` | `# ──── get_user() ────` | `TestGetUser` |
| `update_user()` | `# ──── update_user() ────` | `TestUpdateUser` |
| `reset_user()` | `# ──── reset_user() ────` | `TestResetUser` |
| `authenticate()` | `# ──── authenticate() ────` | `TestAuthenticate` |
| `respond_to_challenge()` | `# ──── respond_to_challenge() ────` | `TestRespondToChallenge` |
| `refresh_tokens()` | `# ──── refresh_tokens() ────` | `TestRefreshTokens` |
| `revoke_tokens()` | `# ──── revoke_tokens() ────` | `TestRevokeTokens` |

Rules:

- Use the provider protocol method name in the section header.
- Use a human-readable PascalCase class name derived from the method name.
- Do not name classes after external SDK operations unless the provider method itself has that name.
- Put method sections in provider protocol order.
- Put shared parser/response tests at the end under `Provider Responses`.

---

## Test ordering inside each provider-method class

Inside each class, use this order:

1. primary success path that asserts exact external payload and returned provider model
2. meaningful success variants that change external call sequence, optional arguments, defaults, clamping, omitted fields, branch, or return model
3. invalid provider input cases that are checked before external calls
4. method-specific response parsing or invalid upstream response cases, if scoped to this method
5. provider/client error mapping for the first external operation
6. provider/client error mapping for later external operations in call sequence, in call order
7. idempotent/swallowed provider errors, if applicable

Do not scatter error tests among success variants. Do not add separate tests for every optional value or enum unless it changes the external payload, call sequence, or return shape.

---

## Standard test method names

Use concise, behavior-first names. Provider test method names should look like integration test names: the class already names the provider method, so the test name should not repeat the resource or operation unless doing so removes ambiguity.

### Success names

| Situation | Test name |
|---|---|
| Standard model result | `test_returns_<result>` |
| Page result | `test_returns_page` |
| Empty page | `test_returns_empty_page` |
| No-return operation | `test_returns_none` or `test_completes` |
| Alternate provider response branch | `test_returns_<branch>` |
| Cursor from upstream result | `test_returns_cursor_from_last_<source>` |
| Multi-step action result | `test_returns_<result>` |
| Accepted alternate input form | `test_accepts_<input_form>` |

Examples:

- `test_returns_user`
- `test_returns_page`
- `test_returns_tokens`
- `test_returns_password_challenge`
- `test_returns_new_mfa_challenge`
- `test_returns_none`
- `test_accepts_encoded_cursor`

Rules:

- Keep success names stable, short, and behavioral.
- Do not use names such as `test_users_uses_expected_payload_and_returns_user` or `test_uses_expected_payload_and_returns_user`. The surrounding `TestListUsers`, `TestGetUser`, or `TestAuthenticate` class already identifies the provider method.
- A success test may still assert the exact external client payload; that does not need to appear in the test name.
- Use `returns_<model_or_branch>` for provider protocol return models and branch names, not API response names.
- Use `test_returns_page` for paginated provider methods unless one class contains multiple page shapes.
- Use separate success tests for distinct external call sequences or distinct return branches.
- Parametrize only when cases share the same structure and assertions.

### Input preparation and external-call shaping names

Use one naming family for tests where the important behavior is not the returned model but the prepared value or external request shape. Prefer `test_passes_...` whenever the provider sends a value, payload, or option to the external client after applying defaults, bounds, normalization, encoding, formatting, or other preparation. Prefer `test_omits_...` only when the contract is that the external request must not contain a field.

| Situation | Test name |
|---|---|
| Prepared argument or request value | `test_passes_<prepared_field>` |
| Prepared value with an important source | `test_passes_<prepared_field>_from_<source>` |
| Optional value included only when supplied | `test_passes_<field>_when_provided` |
| Optional/default field intentionally omitted | `test_omits_<field>` |
| Omission depends on input state | `test_omits_<field>_when_<condition>` |
| False/zero/empty value intentionally preserved | `test_passes_<field>_<value>` |
| Bound/default/normalized/encoded/formatted scalar | `test_passes_<prepared_field>` |
| Prepared filter/query fragment | `test_passes_<concept>_filter` |
| Prepared request body branch | `test_passes_<branch>_payload` |
| Multi-step provider method request shaping | `test_passes_<step>_payload` |

Examples:

- `test_passes_default_limit`
- `test_omits_cursor`
- `test_passes_cursor_when_provided`
- `test_omits_email_when_none`
- `test_passes_enabled_false`
- `test_passes_bounded_limit`
- `test_passes_normalized_email`
- `test_passes_encoded_user_id`
- `test_passes_formatted_expires_at`
- `test_passes_status_filter`
- `test_passes_role_update_payload`

Rules:

- Use these names only when input preparation or request shaping is the point of the test. If the primary success test already proves the ordinary payload shape, name it `test_returns_<result>` and assert the payload inside the test.
- Use `test_passes_...` as the default verb for external-call shaping. It covers defaults, bounds, normalization, encoding, decoding, formatting, filters, and branch payloads.
- Encode the important outcome in the noun phrase: `default_limit`, `bounded_limit`, `normalized_email`, `encoded_user_id`, `formatted_expires_at`, `status_filter`, `role_update_payload`.
- Use `test_omits_...` only for negative request-shape contracts where absence matters. Do not create separate verbs such as `uses`, `clamps`, or `formats` for provider input preparation.
- Use `test_accepts_...` only when the input form itself is the contract and it produces the same ordinary behavior, such as accepting an encoded cursor, alias, or alternate identifier.
- Keep names generic enough to reuse across services, but specific enough to identify the prepared field or request branch.
- Do not combine unrelated transformations in one test merely to reduce line count. Combine only when they are part of one request-shaping branch.

### Error mapping names

Use:

- `test_maps_provider_errors`
- `test_is_idempotent`

Rules:

- Prefix with the external step when a provider method performs multiple external operations and each step can fail.
- The step name should be semantic and concise: `get_user`, `set_password`, `role_assignment`, `enabled_update`, `verify_token`, `challenge`.
- Configure all preceding successful external calls before the failing call.
- Assert only the raised domain error unless a call assertion is necessary to prove no external call occurred after invalid input.

### Invalid/invariant names

Use:

- `test_rejects_invalid_<field>`
- `test_rejects_invalid_<concept>`
- `test_rejects_missing_or_multiple_<fields>`
- `test_rejects_unexpected_provider_response_shape`
- `test_rejects_unexpected_<resource>_shape`
- `test_rejects_invalid_<resource>_payload`
- `test_rejects_unsupported_<concept>`
- `test_normalizes_datetimes_to_utc`

Rules:

- Use invalid/invariant tests only for provider-level checks and upstream response parsing.
- Do not copy endpoint request-validation cases from `payloads.py` into provider tests unless the provider itself validates them.
- For invalid input checked before external access, assert the fake/stubber received no calls when practical.

---

## Success-path standards

A success test should follow arrange/act/assert.

```python
def test_returns_resource(
    self,
    provider: provider_module.ConcreteProvider,
    stubber: Stubber,
) -> None:
    stubber.add_response(
        "external_operation",
        upstream_resource_response(),
        resource_params(),
    )

    result = provider.get_resource(id=RESOURCE_ID)

    assert result == expected_resource()
```

For fake clients:

```python
def test_returns_page(self) -> None:
    client = FakeSearchClient({"hits": {"hits": [resource_hit()]}})
    provider = make_provider(client)

    result = provider.list_resources(user=USER_ID, q="report", limit=10)

    assert client.calls == [
        {
            "index": INDEX,
            "body": list_resources_body(user=USER_ID, q="report", limit=10),
        }
    ]
    assert result == ResourcePage(resources=[expected_resource()], cursor=None)
```

Rules:

- Arrange stubbed external responses before calling the provider method.
- Act once.
- Assert the exact external request payload either through the stubber's `expected_params` or fake client call log.
- Assert exact provider model equality for return values.
- For methods returning `None`, assert the expected external request and `result is None` only when useful; otherwise successful completion with stubber verification is enough.
- For multi-step provider methods, stub and assert every external call in order.
- Do not assert private provider fields unless they are required to compute an expected external payload and no public behavior exposes them. Prefer a helper that uses the provider's deterministic private helper only when that helper is part of the provider's external request contract, such as a secret hash.
- Use ordinary valid inputs in the primary success test.
- Use separate tests for defaults, clamping, omitted optional fields, false/disabled branches, follow-up challenge branches, cursor branches, or other request-shaping behavior when those behaviors are not already clearly covered by the primary success test.

---

## Multi-step provider method standards

Some provider methods orchestrate several external calls. Test the full sequence in the primary success path and isolate failures by step.

Example shape:

```python
def test_returns_credentials(
    self,
    provider: provider_module.ConcreteProvider,
    stubber: Stubber,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "TempPassword123!"
    monkeypatch.setattr(provider_module, "generate_password", lambda: password)

    stub_get_resource(stubber)
    stubber.add_response("set_password", {}, set_password_params(password=password))
    stubber.add_response("set_mfa", {}, set_mfa_params())
    stubber.add_response("global_sign_out", {}, sign_out_params())

    result = provider.reset_resource(id=RESOURCE_ID)

    assert result == ResourceCreds(id=RESOURCE_ID, password=password)
```

Rules:

- Patch nondeterministic functions such as password generation, UUID generation, and current time.
- Keep helper stubs small and named after the external step only when used in multiple tests.
- For each external step that can raise mapped errors, add a separate mapping test with prior steps stubbed successfully.
- Do not test later steps when an earlier step fails unless the provider intentionally continues after that failure.

---

## Branching and alternate response standards

Cover alternate branches when the provider implementation changes the returned provider model or external call sequence.

Examples of valid branches:

- token result versus challenge result
- one challenge type requiring a follow-up external call
- role/admin lookup changing provider model role
- `enabled=False` creating or updating a disabled resource
- optional role assignment requiring a separate external call
- default limit omitted versus explicit limit
- high limit clamped to max
- cursor omitted versus cursor supplied
- empty upstream page versus populated page

Rules:

- Use parametrization when branches differ only by a small input/expected model pair.
- Use separate tests when branches have different external call sequences.
- Do not add one test for every enum value unless every enum value has distinct provider behavior.

---

## Parametrization standards

Use `pytest.mark.parametrize` when multiple cases have the same test shape and assertion style.

Rules:

- Every case must use `pytest.param(..., id="kebab-case")`.
- Parameter names should be semantic: `code`, `provider_error`, `expected_error`, `challenge_name`, `expected_challenge`, `invalid_cursor`, `body`, `expected_params`.
- For upstream error mapping, parameterize over upstream error code or exception instance and expected domain exception type.
- For invalid cursors or unsupported upstream responses, parameterize only when every case has the same expected exception and call behavior.
- Do not parametrize unrelated provider branches just to reduce line count.
- Avoid loops inside tests when parametrization is clearer.

Example:

```python
@pytest.mark.parametrize(
    ("code", "expected_error"),
    [
        pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
        pytest.param("TooManyRequestsException", DomainRateLimited, id="too-many-requests"),
    ],
)
def test_maps_provider_errors(
    self,
    provider: provider_module.ConcreteProvider,
    stubber: Stubber,
    code: str,
    expected_error: type[Exception],
) -> None:
    add_provider_error(
        stubber,
        method="external_operation",
        code=code,
        expected_params=resource_params(),
    )

    with pytest.raises(expected_error):
        provider.get_resource(id=RESOURCE_ID)
```

---

## Provider error mapping standards

Provider error tests should prove that concrete external/client failures are translated to domain exceptions.

For botocore-style clients:

```python
def add_provider_error(
    stubber: Stubber,
    *,
    method: str,
    code: str,
    expected_params: dict[str, Any],
) -> None:
    stubber.add_client_error(
        method,
        service_error_code=code,
        service_message="provider error",
        http_status_code=400,
        expected_params=expected_params,
    )
```

For fake clients:

```python
def test_maps_provider_errors(
    self,
    provider_error: Exception,
    expected_error: type[Exception],
) -> None:
    provider = make_provider(RaisingSearchClient(provider_error))

    with pytest.raises(expected_error):
        provider.list_resources(user=USER_ID)
```

Rules:

- Use valid provider method input so the external call is reached.
- Configure the exact external client operation used by the provider method.
- Assert `pytest.raises(expected_error)` where `expected_error` is a domain exception type.
- Include all upstream errors explicitly mapped by the provider's exception map or `except` clauses.
- Do not assert error messages unless the provider contract explicitly preserves or sets them.
- Do not assert logs, stack traces, or private exception-map internals.
- For multi-step methods, configure preceding steps as success and fail the target step.
- If an operation intentionally swallows an external error, assert the idempotent return and the exact external request that produced the swallowed error.

---

## Response parsing and invariant standards

Provider tests should cover invalid upstream response shapes because providers are the boundary between untrusted external systems and typed domain models.

Use a final `Provider Responses` class when response parsing helpers are shared across methods or when tests focus on private parser behavior visible through public provider methods.

Valid cases include:

- missing required top-level upstream keys
- missing required nested fields
- unsupported upstream enum/challenge/status values
- invalid model payload after decoding
- unexpected result response when the provider expects either token/challenge/page/model
- invalid cursor encoding or decoded cursor shape
- datetime normalization to UTC
- encoded ID/name decoding failures if the provider converts them into domain invariant errors

Rules:

- Prefer exercising response parsing through a public provider method.
- Do not call private parser methods unless the parser is otherwise impossible to reach and the behavior is central to the provider contract.
- Use `DomainInvariantViolation` or the actual domain error raised by the implementation.
- Build invalid responses by minimally modifying a valid response when possible.
- For invalid input that should be rejected before external calls, assert that the fake client call log is empty.
- Do not test Pydantic or data-model internals beyond the provider's responsibility to catch or translate invalid upstream data.

---

## External payload construction standards

The most important assertion in provider tests is the exact external payload. Be precise.

Cover the following when implemented by the provider:

- encoded IDs and encoded names
- secret hashes, signatures, or auth parameters
- external pool/table/index/client identifiers
- optional fields omitted rather than sent as `None`
- optional fields explicitly sent as `False`, `0`, or empty list when that is the contract
- limits and clamping
- pagination/cursor tokens and decoded cursor values
- date/time formatting and timezone normalization
- query/filter construction
- sort order
- role/group assignment calls
- multi-step action calls in exact order
- nested challenge or token response payloads

Rules:

- Assert external payloads as exact dictionaries.
- Avoid partial `in` assertions unless the upstream SDK injects nondeterministic fields that cannot be controlled.
- Keep expected payloads close to the test. Use helpers for nested/repeated payloads only.
- If the provider uses a deterministic private helper to produce a cryptographic/signature field, the expected payload may call that helper on the provider instance. Do not reimplement cryptographic logic in the test unless it is simple and clearer.

---

## Validation boundaries: provider tests versus integration tests

Provider tests should not become endpoint tests.

Provider tests may cover:

- invalid provider method arguments only when the provider method itself validates them
- invalid cursors or encoded values parsed inside the provider
- invalid upstream response shapes
- unsupported upstream challenge/status/result values
- provider-level invariant violations

Provider tests should not cover:

- missing HTTP request body fields
- request aliases or camelCase API field names
- HTTP status codes or problem response bodies
- authentication or authorization rules in `service.py`
- route matching or unsupported HTTP methods
- payload model request validators, unless the provider directly uses the same model internally

Use `payloads.py` to understand names and semantics, but do not copy its endpoint validation matrix into provider tests.

---

## Shared `conftest.py` guidance

Use existing shared fixtures when possible. Propose edits to `conftest.py` only when the need is generic and likely to recur across provider tests for multiple services.

Appropriate generic additions:

- environment isolation for a broadly used SDK, if every provider suite needs it
- a generic fake clock fixture
- a generic deterministic UUID/password/token fixture only if multiple services share it
- a reusable local no-network guard, if available in the project style

Do not move these into `conftest.py`:

- concrete provider fixtures
- service-specific external clients
- SDK stubbers for a specific provider
- service-specific IDs, encoded values, pools, tables, indexes, tokens, sessions, or payloads
- provider-specific fake clients
- provider-specific upstream response factories
- provider-specific error parameter sets

If a generic fixture is missing, propose the smallest additive change. Do not invent service-specific wrappers.

---

## Shared `helpers.py` guidance

The shared helper layer should remain small. Provider tests should usually use local helpers because external payloads are service-specific.

Expected generic helpers may include:

- small response/assertion helpers for integration tests
- `ProviderMethod` for fake provider methods in handler/integration tests
- tiny generic utilities that are truly cross-service and semantically meaningful

Propose edits to `helpers.py` only for helpers that are:

1. generic across services
2. repetitive across several provider test files
3. semantically meaningful
4. clearer than inline assertions or local helpers

Appropriate helper candidates:

- a generic botocore `add_client_error` wrapper if many provider suites repeat the exact same shape
- a generic deterministic no-network guard if applicable
- a small assertion for standardized provider-call fakes if multiple non-SDK clients use the same pattern

Inappropriate helper candidates:

- external payload factories
- upstream response factories
- provider model factories
- concrete provider fakes
- endpoint-specific or provider-specific invalid payload lists
- wrappers that hide the provider method call or external operation being tested
- helpers that save one or two lines but obscure the provider contract

Prefer inline code for one-off values. Prefer local helpers for repeated provider-specific construction. Prefer shared helpers only for cross-service testing primitives.

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
- Assert exact external request dictionaries.
- Assert exact provider model returns.
- Keep request payload and upstream response helpers local and semantically named.
- Keep comments limited to section headers and rare non-obvious provider constraints.
- Do not add hundreds of helpers. Add helpers only where they remove repeated, semantically meaningful code.
- Do not hide important provider behavior behind generic wrappers.
- Do not use real external services.
- Do not test private service internals.

The generated file should be minimal but not under-specified. A reader should be able to understand the provider protocol contract and external-client contract without opening the implementation.

---

## How to derive the suite from the supplementary files

Inspect in this order:

1. Provider protocol/implementation modules
   - protocol method names and signatures
   - concrete provider classes
   - provider model classes
   - external clients and constructor arguments
   - external operation names and payload construction
   - encoding/decoding helpers
   - default values, clamping, cursor handling, date formatting
   - response parsing helpers
   - exception maps and `except` clauses

2. `service.py`
   - which provider methods are actually used
   - semantic meaning of method arguments
   - provider-level branches that service depends on
   - idempotent behavior delegated to provider versus handled in service

3. `payloads.py`
   - domain field names and enum meanings
   - response model shape only as context for provider model semantics
   - do not copy endpoint request validation into provider tests

4. `handler.py`
   - only to confirm which concrete provider constructors are used and which provider modules belong to the service
   - do not derive HTTP tests here

5. `conftest.py` and `helpers.py`
   - reusable environment/test primitives
   - avoid moving service-specific provider logic into shared fixtures/helpers

Do not test private service internals directly. Do not test HTTP behavior. Test concrete provider methods directly.

---

## Provider coverage checklist

For each concrete provider test file, ensure the final file covers the applicable items:

- `pytestmark = pytest.mark.unit`
- standardized import order
- `Helpers` section with only meaningful local helpers
- deterministic constants for repeated IDs/timestamps/external identifiers
- provider fixture or `make_provider` helper that avoids real external calls
- SDK stubber or tiny fake client for the external dependency
- one class per provider protocol method
- section headers with exact provider method names
- primary success path for each provider method
- exact external operation payloads and call order
- exact provider model returned on success
- meaningful alternate success branches
- provider defaults, clamping, cursor, date, encoding, and optional-field behavior where implemented
- invalid provider input/invariant behavior where implemented
- invalid upstream response parsing where implemented
- every mapped external/client error for each provider method or external step
- idempotent/swallowed external errors where implemented
- no handler/service/lambda/API Gateway invocation
- no route/auth/status/body assertions
- no real external service usage
- no excessive helpers or opaque abstraction

---

## Done criteria

A completed `test_<provider>.py` should satisfy all of the following:

- It is a provider unit test file, not an integration test file.
- It directly instantiates or constructs the concrete provider under test.
- It uses stubbers or tiny fakes to prevent real external calls.
- It calls provider protocol methods directly.
- It asserts exact external client payloads for success paths.
- It asserts exact provider model objects returned by provider methods.
- It covers all meaningful provider branches and response shapes.
- It covers external error-to-domain-error mapping.
- It covers invalid upstream response handling and provider invariant violations where implemented.
- It keeps service-specific factories, fakes, constants, and payload helpers local.
- It proposes shared helper or `conftest.py` edits only for generic, recurring, semantically useful primitives.
- It is concise, standardized, and readable as the provider contract.
