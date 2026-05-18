from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
import pytest
import user.providers.user as provider_module
from botocore.stub import Stubber
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.providers.cognito import encode_id, encode_name
from user.providers.user import User, UserCreds, UserPage

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

REGION = "us-east-1"
USER_POOL_ID = "pool-id"
USER_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_ID = "22222222-2222-2222-2222-222222222222"
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, tzinfo=timezone.utc)
PASSWORD = "TempPass#2026"

PROVIDER_ERROR_CASES = [
    pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
    pytest.param("NotAuthorizedException", DomainForbidden, id="not-authorized"),
    pytest.param("TooManyRequestsException", DomainRateLimited, id="too-many-requests"),
    pytest.param("LimitExceededException", DomainRateLimited, id="limit-exceeded"),
    pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
    pytest.param("ResourceNotFoundException", DomainNotFound, id="resource-not-found"),
]


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


def user_attributes(
    *,
    name: str = "alice",
) -> list[dict[str, str]]:
    return [
        {
            "Name": "preferred_username",
            "Value": encode_name(name),
        },
        {
            "Name": "name",
            "Value": name,
        },
    ]


def cognito_list_user(
    *,
    id: str = USER_ID,
    name: str = "alice",
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
) -> dict[str, Any]:
    return {
        "Username": encode_id(id),
        "Enabled": enabled,
        "UserCreateDate": created_at,
        "UserLastModifiedDate": updated_at,
        "Attributes": user_attributes(name=name),
    }


def cognito_get_user(
    *,
    id: str = USER_ID,
    name: str = "alice",
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
) -> dict[str, Any]:
    return {
        "Username": encode_id(id),
        "Enabled": enabled,
        "UserCreateDate": created_at,
        "UserLastModifiedDate": updated_at,
        "UserAttributes": user_attributes(name=name),
    }


def expected_user(
    *,
    id: str = USER_ID,
    name: str = "alice",
    role: User.Role = User.Role.USER,
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
    last_login_at: datetime | None = None,
) -> User:
    return User(
        id=id,
        name=name,
        role=role,
        enabled=enabled,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=last_login_at,
    )


def get_user_params(id: str = USER_ID) -> dict[str, str]:
    return {
        "UserPoolId": USER_POOL_ID,
        "Username": encode_id(id),
    }


def group_params(id: str = USER_ID) -> dict[str, str]:
    return {
        "UserPoolId": USER_POOL_ID,
        "Username": encode_id(id),
    }


def stub_get_user(
    stubber: Stubber,
    *,
    id: str = USER_ID,
    name: str = "alice",
    role: User.Role = User.Role.USER,
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
) -> None:
    stubber.add_response(
        "admin_get_user",
        cognito_get_user(
            id=id,
            name=name,
            enabled=enabled,
            created_at=created_at,
            updated_at=updated_at,
        ),
        get_user_params(id),
    )
    stubber.add_response(
        "admin_list_groups_for_user",
        {
            "Groups": [
                {
                    "GroupName": "admin",
                }
            ]
            if role is User.Role.ADMIN
            else [],
        },
        group_params(id),
    )


# ──── Fixtures ────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@pytest.fixture
def cognito_client():
    return boto3.client("cognito-idp", region_name=REGION)


@pytest.fixture
def provider(
    monkeypatch: pytest.MonkeyPatch,
    cognito_client,
) -> provider_module.CognitoUserProvider:
    monkeypatch.setattr(
        provider_module.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )
    return provider_module.CognitoUserProvider(
        region=REGION,
        user_pool_id=USER_POOL_ID,
    )


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber


# ──── list_users() ────────────────────────────────────────────────────────────────────


class TestListUsers:
    def test_returns_page(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [
                    cognito_list_user(id=USER_ID, name="alice"),
                    cognito_list_user(id=ADMIN_ID, name="admin"),
                ],
                "PaginationToken": "next-cursor",
            },
            {
                "UserPoolId": USER_POOL_ID,
                "Limit": 10,
                "Filter": 'name ^= "alice"',
                "PaginationToken": "users-cursor",
            },
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            {"Groups": []},
            group_params(USER_ID),
        )
        stubber.add_response(
            "admin_list_groups_for_user",
            {"Groups": [{"GroupName": "admin"}]},
            group_params(ADMIN_ID),
        )

        result = provider.list_users(q="alice", limit=10, cursor="users-cursor")

        assert result == UserPage(
            users=[
                expected_user(id=USER_ID, name="alice", role=User.Role.USER),
                expected_user(id=ADMIN_ID, name="admin", role=User.Role.ADMIN),
            ],
            cursor="next-cursor",
        )

    def test_passes_default_limit(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {"Users": []},
            {
                "UserPoolId": USER_POOL_ID,
                "Limit": 25,
            },
        )

        result = provider.list_users()

        assert result == UserPage(users=[], cursor=None)

    def test_passes_bounded_limit(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {"Users": []},
            {
                "UserPoolId": USER_POOL_ID,
                "Limit": 60,
            },
        )

        provider.list_users(limit=999)

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="list_users",
            code=code,
            expected_params={
                "UserPoolId": USER_POOL_ID,
                "Limit": 25,
            },
        )

        with pytest.raises(expected_error):
            provider.list_users()


# ──── create_user() ───────────────────────────────────────────────────────────────────


class TestCreateUser:
    def test_returns_user(
        self,
        monkeypatch: pytest.MonkeyPatch,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        monkeypatch.setattr(provider_module, "generate_id", lambda: USER_ID)

        stubber.add_response(
            "admin_create_user",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": encode_name("alice"),
                    },
                    {
                        "Name": "name",
                        "Value": "alice",
                    },
                ],
                "MessageAction": "SUPPRESS",
            },
        )
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.USER)

        result = provider.create_user(name="alice", role=User.Role.USER)

        assert result == expected_user(id=USER_ID, name="alice", role=User.Role.USER)

    def test_returns_admin_user(
        self,
        monkeypatch: pytest.MonkeyPatch,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        monkeypatch.setattr(provider_module, "generate_id", lambda: USER_ID)

        stubber.add_response(
            "admin_create_user",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": encode_name("alice"),
                    },
                    {
                        "Name": "name",
                        "Value": "alice",
                    },
                ],
                "MessageAction": "SUPPRESS",
            },
        )
        stubber.add_response(
            "admin_add_user_to_group",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "GroupName": "admin",
            },
        )
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.ADMIN)

        result = provider.create_user(name="alice", role=User.Role.ADMIN)

        assert result == expected_user(id=USER_ID, name="alice", role=User.Role.ADMIN)

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        monkeypatch.setattr(provider_module, "generate_id", lambda: USER_ID)

        add_provider_error(
            stubber,
            method="admin_create_user",
            code=code,
            expected_params={
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": encode_name("alice"),
                    },
                    {
                        "Name": "name",
                        "Value": "alice",
                    },
                ],
                "MessageAction": "SUPPRESS",
            },
        )

        with pytest.raises(expected_error):
            provider.create_user(name="alice", role=User.Role.USER)


# ──── get_user() ──────────────────────────────────────────────────────────────────────


class TestGetUser:
    def test_returns_user(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.USER)

        result = provider.get_user(id=USER_ID)

        assert result == expected_user(id=USER_ID, name="alice", role=User.Role.USER)

    def test_normalizes_datetimes_to_utc(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        local_tz = timezone(timedelta(hours=9))
        stub_get_user(
            stubber,
            id=USER_ID,
            name="alice",
            role=User.Role.USER,
            created_at=datetime(2026, 1, 1, 10, tzinfo=local_tz),
            updated_at=datetime(2026, 1, 2, 10, tzinfo=local_tz),
        )

        result = provider.get_user(id=USER_ID)

        assert result == expected_user(
            id=USER_ID,
            name="alice",
            role=User.Role.USER,
            created_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 2, 1, tzinfo=timezone.utc),
        )

    def test_rejects_unexpected_provider_response_shape(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "admin_get_user",
            {
                "Username": encode_id(USER_ID),
            },
            get_user_params(USER_ID),
        )

        with pytest.raises(
            DomainInvariantViolation, match="Unexpected cognito response"
        ):
            provider.get_user(id=USER_ID)

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="admin_get_user",
            code=code,
            expected_params=get_user_params(USER_ID),
        )

        with pytest.raises(expected_error):
            provider.get_user(id=USER_ID)


# ──── update_user() ───────────────────────────────────────────────────────────────────


class TestUpdateUser:
    def test_returns_user(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "admin_update_user_attributes",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": encode_name("alice"),
                    },
                    {
                        "Name": "name",
                        "Value": "alice",
                    },
                ],
            },
        )
        stubber.add_response(
            "admin_add_user_to_group",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "GroupName": "admin",
            },
        )
        stubber.add_response(
            "admin_disable_user",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
            },
        )
        stub_get_user(
            stubber,
            id=USER_ID,
            name="alice",
            role=User.Role.ADMIN,
            enabled=False,
        )

        result = provider.update_user(
            id=USER_ID,
            name="alice",
            role=User.Role.ADMIN,
            enabled=False,
        )

        assert result == expected_user(
            id=USER_ID,
            name="alice",
            role=User.Role.ADMIN,
            enabled=False,
        )

    def test_returns_user_without_optional_updates(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.USER)

        result = provider.update_user(id=USER_ID)

        assert result == expected_user(id=USER_ID, name="alice", role=User.Role.USER)

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_name_update_provider_errors(
        self,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="admin_update_user_attributes",
            code=code,
            expected_params={
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "UserAttributes": [
                    {
                        "Name": "preferred_username",
                        "Value": encode_name("alice"),
                    },
                    {
                        "Name": "name",
                        "Value": "alice",
                    },
                ],
            },
        )

        with pytest.raises(expected_error):
            provider.update_user(id=USER_ID, name="alice")


# ──── reset_user() ────────────────────────────────────────────────────────────────────


class TestResetUser:
    def test_returns_credentials(
        self,
        monkeypatch: pytest.MonkeyPatch,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        monkeypatch.setattr(provider_module, "generate_password", lambda: PASSWORD)
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.USER)
        stubber.add_response(
            "admin_set_user_password",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "Password": PASSWORD,
                "Permanent": False,
            },
        )
        stubber.add_response(
            "admin_set_user_mfa_preference",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "SoftwareTokenMfaSettings": {
                    "Enabled": False,
                    "PreferredMfa": False,
                },
            },
        )
        stubber.add_response(
            "admin_user_global_sign_out",
            {},
            {
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
            },
        )

        result = provider.reset_user(id=USER_ID)

        assert result == UserCreds(name="alice", password=PASSWORD)

    @pytest.mark.parametrize(
        ("code", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_set_password_provider_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        provider: provider_module.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        monkeypatch.setattr(provider_module, "generate_password", lambda: PASSWORD)
        stub_get_user(stubber, id=USER_ID, name="alice", role=User.Role.USER)
        add_provider_error(
            stubber,
            method="admin_set_user_password",
            code=code,
            expected_params={
                "UserPoolId": USER_POOL_ID,
                "Username": encode_id(USER_ID),
                "Password": PASSWORD,
                "Permanent": False,
            },
        )

        with pytest.raises(expected_error):
            provider.reset_user(id=USER_ID)
