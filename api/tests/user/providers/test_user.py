from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import pytest
import user.providers.user as user
from botocore.stub import Stubber
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from user.providers.user import User, UserPage

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


def list_users_params(
    *,
    q: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    q = q.replace("\\", "\\\\").replace('"', '\\"') if q else None

    return {
        "UserPoolId": "pool-id",
        "Limit": min(limit or 25, 60),
        **({"Filter": f'preferred_username ^= "{q}"'} if q else {}),
        **({"PaginationToken": cursor} if cursor else {}),
    }


def cognito_user_response(
    *,
    id: str = "user-1",
    name: str = "Alice",
    enabled: bool = True,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    for_admin_get_user: bool = False,
) -> dict[str, Any]:
    created_at = created_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
    updated_at = updated_at or datetime(2026, 1, 2, tzinfo=timezone.utc)
    attrs_key = "UserAttributes" if for_admin_get_user else "Attributes"

    return {
        "Username": id,
        "Enabled": enabled,
        "UserCreateDate": created_at,
        "UserLastModifiedDate": updated_at,
        attrs_key: [
            {
                "Name": "preferred_username",
                "Value": name,
            }
        ],
    }


def role_response(*, is_admin: bool) -> dict[str, list[dict[str, str]]]:
    groups = [{"GroupName": "admin"}] if is_admin else [{"GroupName": "user"}]
    return {"Groups": groups}


def add_client_error(
    stubber: Stubber,
    *,
    method: str,
    service_error_code: str,
    expected_params: dict[str, Any],
    service_message: str = "provider error",
    http_status_code: int = 400,
) -> None:
    stubber.add_client_error(
        method,
        service_error_code=service_error_code,
        service_message=service_message,
        http_status_code=http_status_code,
        expected_params=expected_params,
    )


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Prevent boto3 from attempting to discover real AWS credentials.

    These tests use botocore Stubber, so no real AWS calls are made, but boto3
    still needs credentials available when constructing/signing requests.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name="us-east-1")


@pytest.fixture
def provider(
    monkeypatch: pytest.MonkeyPatch,
    cognito_client,
) -> user.CognitoUserProvider:
    monkeypatch.setattr(
        user.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )

    return user.CognitoUserProvider(
        region="us-east-1",
        user_pool_id="pool-id",
    )


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber


@pytest.fixture
def user_record() -> User:
    return User(
        id="user-1",
        name="Alice",
        role=User.Role.USER,
        enabled=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        last_login_at=None,
    )


@pytest.fixture
def admin_record() -> User:
    return User(
        id="admin-1",
        name="Admin",
        role=User.Role.ADMIN,
        enabled=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        last_login_at=None,
    )


@pytest.fixture
def disabled_admin_record() -> User:
    return User(
        id="user-1",
        name="Alice Updated",
        role=User.Role.ADMIN,
        enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        last_login_at=None,
    )


@pytest.fixture
def user_page(
    user_record: User,
    admin_record: User,
) -> UserPage:
    return UserPage(
        users=[
            user_record,
            admin_record,
        ],
        cursor="next-cursor",
    )


# ──── Tests ───────────────────────────────────────────────────────────────────────────


# ──── list_users() ────────────────────────────────────────────────────────────────────


class TestListUsers:
    def test_uses_expected_payload_and_returns_user_page(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        user_page: UserPage,
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [
                    cognito_user_response(id="user-1", name="Alice"),
                    cognito_user_response(id="admin-1", name="Admin"),
                ],
                "PaginationToken": "next-cursor",
            },
            list_users_params(q="ali", limit=10, cursor="cursor-1"),
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=True),
            {
                "UserPoolId": "pool-id",
                "Username": "admin-1",
            },
        )

        result = provider.list_users(
            q="ali",
            limit=10,
            cursor="cursor-1",
        )

        assert result == user_page

    def test_uses_default_limit_when_limit_is_omitted(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [],
            },
            list_users_params(),
        )

        result = provider.list_users()

        assert result == UserPage(users=[], cursor=None)

    def test_escapes_query_and_clamps_limit(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        query = 'ali\\ce"name'

        stubber.add_response(
            "list_users",
            {
                "Users": [
                    cognito_user_response(),
                ],
            },
            list_users_params(q=query, limit=200),
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.list_users(q=query, limit=200)

        assert result.users[0].id == "user-1"

    def test_returns_empty_page_when_provider_returns_no_users(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [],
                "PaginationToken": "next-cursor",
            },
            list_users_params(limit=10),
        )

        result = provider.list_users(limit=10)

        assert result == UserPage(users=[], cursor="next-cursor")

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
            pytest.param(
                "NotAuthorizedException",
                DomainForbidden,
                id="not-authorized",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
            pytest.param(
                "ResourceNotFoundException",
                DomainNotFound,
                id="resource-not-found",
            ),
        ],
    )
    def test_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="list_users",
            service_error_code=service_error_code,
            expected_params=list_users_params(),
        )

        with pytest.raises(expected_error):
            provider.list_users()


# ──── get_user() ─────────────────────────────────────────────────────────────────────


class TestGetUser:
    def test_uses_expected_payload_and_returns_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        user_record: User,
    ) -> None:
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(for_admin_get_user=True),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.get_user(id="user-1")

        assert result == user_record

    def test_returns_admin_role_when_user_is_in_admin_group(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        admin_record: User,
    ) -> None:
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(
                id="admin-1",
                name="Admin",
                for_admin_get_user=True,
            ),
            {
                "UserPoolId": "pool-id",
                "Username": "admin-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=True),
            {
                "UserPoolId": "pool-id",
                "Username": "admin-1",
            },
        )

        result = provider.get_user(id="admin-1")

        assert result == admin_record

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
            pytest.param(
                "NotAuthorizedException",
                DomainForbidden,
                id="not-authorized",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
            pytest.param(
                "ResourceNotFoundException",
                DomainNotFound,
                id="resource-not-found",
            ),
        ],
    )
    def test_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="admin_get_user",
            service_error_code=service_error_code,
            expected_params={
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        with pytest.raises(expected_error):
            provider.get_user(id="user-1")


# ──── update_user() ──────────────────────────────────────────────────────────────────


class TestUpdateUser:
    def test_updates_name_role_enabled_and_returns_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        disabled_admin_record: User,
    ) -> None:
        stubber.add_response(
            "admin_update_user_attributes",
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": "Alice Updated",
                    }
                ],
            },
        )
        stubber.add_response(
            "admin_add_user_to_group",
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "GroupName": "admin",
            },
        )
        stubber.add_response(
            "admin_disable_user",
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(
                id="user-1",
                name="Alice Updated",
                enabled=False,
                for_admin_get_user=True,
            ),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=True),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.update_user(
            id="user-1",
            update={
                "name": "Alice Updated",
                "role": User.Role.ADMIN,
                "enabled": False,
            },
        )

        assert result == disabled_admin_record

    def test_updates_name_using_expected_payload_and_returns_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "admin_update_user_attributes",
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": "Alice Updated",
                    }
                ],
            },
        )
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(
                name="Alice Updated",
                for_admin_get_user=True,
            ),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.update_user(
            id="user-1",
            update={"name": "Alice Updated"},
        )

        assert result == User(
            id="user-1",
            name="Alice Updated",
            role=User.Role.USER,
            enabled=True,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            last_login_at=None,
        )

    @pytest.mark.parametrize(
        ("role", "expected_method"),
        [
            pytest.param(User.Role.USER, "admin_remove_user_from_group", id="user"),
            pytest.param(User.Role.ADMIN, "admin_add_user_to_group", id="admin"),
        ],
    )
    def test_updates_role_using_expected_group_method(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        role: User.Role,
        expected_method: str,
    ) -> None:
        stubber.add_response(
            expected_method,
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "GroupName": "admin",
            },
        )
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(for_admin_get_user=True),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=role == User.Role.ADMIN),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.update_user(
            id="user-1",
            update={"role": role},
        )

        assert result.id == "user-1"
        assert result.role == role

    @pytest.mark.parametrize(
        ("enabled", "expected_method"),
        [
            pytest.param(True, "admin_enable_user", id="enable"),
            pytest.param(False, "admin_disable_user", id="disable"),
        ],
    )
    def test_updates_enabled_using_expected_method(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        enabled: bool,
        expected_method: str,
    ) -> None:
        stubber.add_response(
            expected_method,
            {},
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(
                enabled=enabled,
                for_admin_get_user=True,
            ),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.update_user(
            id="user-1",
            update={"enabled": enabled},
        )

        assert result.id == "user-1"
        assert result.enabled is enabled

    def test_with_empty_update_only_returns_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        user_record: User,
    ) -> None:
        stubber.add_response(
            "admin_get_user",
            cognito_user_response(for_admin_get_user=True),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.update_user(
            id="user-1",
            update={},
        )

        assert result == user_record

    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
            pytest.param(
                "NotAuthorizedException",
                DomainForbidden,
                id="not-authorized",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
            pytest.param(
                "ResourceNotFoundException",
                DomainNotFound,
                id="resource-not-found",
            ),
        ],
    )
    def test_name_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method="admin_update_user_attributes",
            service_error_code=service_error_code,
            expected_params={
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": "Alice Updated",
                    }
                ],
            },
        )

        with pytest.raises(expected_error):
            provider.update_user(
                id="user-1",
                update={"name": "Alice Updated"},
            )

    @pytest.mark.parametrize(
        ("role", "method"),
        [
            pytest.param(User.Role.USER, "admin_remove_user_from_group", id="user"),
            pytest.param(User.Role.ADMIN, "admin_add_user_to_group", id="admin"),
        ],
    )
    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
            pytest.param(
                "NotAuthorizedException",
                DomainForbidden,
                id="not-authorized",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
            pytest.param(
                "ResourceNotFoundException",
                DomainNotFound,
                id="resource-not-found",
            ),
        ],
    )
    def test_role_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        role: User.Role,
        method: str,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method=method,
            service_error_code=service_error_code,
            expected_params={
                "UserPoolId": "pool-id",
                "Username": "user-1",
                "GroupName": "admin",
            },
        )

        with pytest.raises(expected_error):
            provider.update_user(
                id="user-1",
                update={"role": role},
            )

    @pytest.mark.parametrize(
        ("enabled", "method"),
        [
            pytest.param(True, "admin_enable_user", id="enable"),
            pytest.param(False, "admin_disable_user", id="disable"),
        ],
    )
    @pytest.mark.parametrize(
        ("service_error_code", "expected_error"),
        [
            pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
            pytest.param(
                "NotAuthorizedException",
                DomainForbidden,
                id="not-authorized",
            ),
            pytest.param(
                "TooManyRequestsException",
                DomainRateLimited,
                id="too-many-requests",
            ),
            pytest.param(
                "LimitExceededException",
                DomainRateLimited,
                id="limit-exceeded",
            ),
            pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
            pytest.param(
                "ResourceNotFoundException",
                DomainNotFound,
                id="resource-not-found",
            ),
        ],
    )
    def test_enabled_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        enabled: bool,
        method: str,
        service_error_code: str,
        expected_error: type[Exception],
    ) -> None:
        add_client_error(
            stubber,
            method=method,
            service_error_code=service_error_code,
            expected_params={
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        with pytest.raises(expected_error):
            provider.update_user(
                id="user-1",
                update={"enabled": enabled},
            )


# ──── Provider Responses ──────────────────────────────────────────────────────────────


class TestResponseParsing:
    @pytest.mark.parametrize(
        "response",
        [
            pytest.param({}, id="empty-response"),
            pytest.param({"Username": "user-1"}, id="missing-required-fields"),
            pytest.param(
                {
                    "Username": "user-1",
                    "Enabled": True,
                    "UserCreateDate": datetime(2026, 1, 1, tzinfo=timezone.utc),
                },
                id="missing-updated-at",
            ),
        ],
    )
    def test_rejects_unexpected_list_user_response(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        response: dict[str, Any],
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [response],
            },
            list_users_params(),
        )

        with pytest.raises(DomainInvariantViolation):
            provider.list_users()

    @pytest.mark.parametrize(
        "response",
        [
            pytest.param({"Username": "user-1"}, id="missing-required-fields"),
            pytest.param(
                {
                    "Username": "user-1",
                    "Enabled": True,
                    "UserCreateDate": datetime(2026, 1, 1, tzinfo=timezone.utc),
                },
                id="missing-updated-at",
            ),
        ],
    )
    def test_rejects_unexpected_get_user_response(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        response: dict[str, Any],
    ) -> None:
        stubber.add_response(
            "admin_get_user",
            response,
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        with pytest.raises(DomainInvariantViolation):
            provider.get_user(id="user-1")

    def test_converts_datetimes_to_utc(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        eastern = timezone(timedelta(hours=-5))

        stubber.add_response(
            "admin_get_user",
            cognito_user_response(
                created_at=datetime(2026, 1, 1, 7, 0, tzinfo=eastern),
                updated_at=datetime(2026, 1, 2, 8, 30, tzinfo=eastern),
                for_admin_get_user=True,
            ),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            role_response(is_admin=False),
            {
                "UserPoolId": "pool-id",
                "Username": "user-1",
            },
        )

        result = provider.get_user(id="user-1")

        assert result.created_at == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert result.updated_at == datetime(2026, 1, 2, 13, 30, tzinfo=timezone.utc)
