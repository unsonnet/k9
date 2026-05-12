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
from shared.providers.cognito import encode_id, encode_name
from user.providers.user import User, UserPage

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

REGION = "us-east-1"
USER_POOL_ID = "pool-id"
USER_ID = "user-1"
ADMIN_ID = "admin-1"
USER_XID = encode_id(USER_ID)
ADMIN_XID = encode_id(ADMIN_ID)
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, tzinfo=timezone.utc)

PROVIDER_ERROR_CASES = [
    pytest.param("ForbiddenException", DomainForbidden, id="forbidden"),
    pytest.param("NotAuthorizedException", DomainForbidden, id="not-authorized"),
    pytest.param("TooManyRequestsException", DomainRateLimited, id="too-many-requests"),
    pytest.param("LimitExceededException", DomainRateLimited, id="limit-exceeded"),
    pytest.param("UserNotFoundException", DomainNotFound, id="user-not-found"),
    pytest.param("ResourceNotFoundException", DomainNotFound, id="resource-not-found"),
]


def user_params(xid: str = USER_XID) -> dict[str, str]:
    return {
        "UserPoolId": USER_POOL_ID,
        "Username": xid,
    }


def group_params(xid: str = USER_XID) -> dict[str, str]:
    return {
        **user_params(xid),
        "GroupName": "admin",
    }


def list_users_params(
    *,
    q: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    return {
        "UserPoolId": USER_POOL_ID,
        "Limit": min(limit or 25, 60),
        **({"Filter": f'name ^= "{q}"'} if q else {}),
        **({"PaginationToken": cursor} if cursor else {}),
    }


def name_update_params(
    *,
    xid: str = USER_XID,
    name: str = "Alice Updated",
) -> dict[str, Any]:
    return {
        **user_params(xid),
        "UserAttributes": [
            {"Name": "preferred_username", "Value": encode_name(name)},
            {"Name": "name", "Value": name},
        ],
    }


def cognito_user(
    *,
    id: str = USER_ID,
    name: str = "Alice",
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
    admin_get_user: bool = False,
) -> dict[str, Any]:
    attrs_key = "UserAttributes" if admin_get_user else "Attributes"
    return {
        "Username": encode_id(id),
        "Enabled": enabled,
        "UserCreateDate": created_at,
        "UserLastModifiedDate": updated_at,
        attrs_key: [
            {"Name": "preferred_username", "Value": encode_name(name)},
            {"Name": "name", "Value": name},
        ],
    }


def groups(*, admin: bool = False) -> dict[str, list[dict[str, str]]]:
    return {"Groups": [{"GroupName": "admin" if admin else "user"}]}


def expected_user(
    *,
    id: str = USER_ID,
    name: str = "Alice",
    role: User.Role = User.Role.USER,
    enabled: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = UPDATED_AT,
) -> User:
    return User(
        id=id,
        name=name,
        role=role,
        enabled=enabled,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


def stub_group_lookup(
    stubber: Stubber, *, xid: str = USER_XID, admin: bool = False
) -> None:
    stubber.add_response(
        "admin_list_groups_for_user",
        groups(admin=admin),
        user_params(xid),
    )


def stub_get_user(
    stubber: Stubber,
    *,
    id: str = USER_ID,
    name: str = "Alice",
    role: User.Role = User.Role.USER,
    enabled: bool = True,
) -> None:
    xid = encode_id(id)
    stubber.add_response(
        "admin_get_user",
        cognito_user(id=id, name=name, enabled=enabled, admin_get_user=True),
        user_params(xid),
    )
    stub_group_lookup(stubber, xid=xid, admin=role == User.Role.ADMIN)


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


# ──── Fixtures ───────────────────────────────────────────────────────────────────────


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
) -> user.CognitoUserProvider:
    monkeypatch.setattr(
        user.boto3,
        "client",
        lambda service_name, region_name=None: cognito_client,
    )
    return user.CognitoUserProvider(region=REGION, user_pool_id=USER_POOL_ID)


@pytest.fixture
def stubber(cognito_client):
    with Stubber(cognito_client) as stubber:
        yield stubber


# ──── list_users() ────────────────────────────────────────────────────────────────────


class TestListUsers:
    def test_uses_expected_payload_and_returns_page(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {
                "Users": [
                    cognito_user(id=USER_ID, name="Alice"),
                    cognito_user(id=ADMIN_ID, name="Admin"),
                ],
                "PaginationToken": "next-cursor",
            },
            list_users_params(q="ali", limit=10, cursor="cursor-1"),
        )
        stub_group_lookup(stubber, xid=USER_XID)
        stub_group_lookup(stubber, xid=ADMIN_XID, admin=True)

        result = provider.list_users(q="ali", limit=10, cursor="cursor-1")

        assert result == UserPage(
            users=[
                expected_user(),
                expected_user(id=ADMIN_ID, name="Admin", role=User.Role.ADMIN),
            ],
            cursor="next-cursor",
        )

    def test_uses_default_limit_and_returns_empty_page(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response("list_users", {"Users": []}, list_users_params())

        result = provider.list_users()

        assert result == UserPage(users=[], cursor=None)

    def test_clamps_limit_to_100(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response(
            "list_users",
            {"Users": [cognito_user()]},
            list_users_params(limit=200),
        )
        stub_group_lookup(stubber)

        result = provider.list_users(limit=200)

        assert result.users == [expected_user()]

    @pytest.mark.parametrize(("code", "expected_error"), PROVIDER_ERROR_CASES)
    def test_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="list_users",
            code=code,
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
    ) -> None:
        stub_get_user(stubber)

        result = provider.get_user(id=USER_ID)

        assert result == expected_user()

    def test_returns_admin_role_when_user_is_in_admin_group(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stub_get_user(stubber, id=ADMIN_ID, name="Admin", role=User.Role.ADMIN)

        result = provider.get_user(id=ADMIN_ID)

        assert result == expected_user(
            id=ADMIN_ID,
            name="Admin",
            role=User.Role.ADMIN,
        )

    @pytest.mark.parametrize(("code", "expected_error"), PROVIDER_ERROR_CASES)
    def test_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="admin_get_user",
            code=code,
            expected_params=user_params(),
        )

        with pytest.raises(expected_error):
            provider.get_user(id=USER_ID)


# ──── update_user() ──────────────────────────────────────────────────────────────────


class TestUpdateUser:
    def test_uses_expected_payload_and_returns_updated_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stubber.add_response("admin_update_user_attributes", {}, name_update_params())
        stubber.add_response("admin_add_user_to_group", {}, group_params())
        stubber.add_response("admin_disable_user", {}, user_params())
        stub_get_user(
            stubber,
            name="Alice Updated",
            role=User.Role.ADMIN,
            enabled=False,
        )

        result = provider.update_user(
            id=USER_ID,
            update={
                "name": "Alice Updated",
                "role": User.Role.ADMIN,
                "enabled": False,
            },
        )

        assert result == expected_user(
            name="Alice Updated",
            role=User.Role.ADMIN,
            enabled=False,
        )

    def test_uses_empty_update_and_returns_user(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        stub_get_user(stubber)

        result = provider.update_user(id=USER_ID, update={})

        assert result == expected_user()

    @pytest.mark.parametrize(
        ("role", "method"),
        [
            pytest.param(User.Role.USER, "admin_remove_user_from_group", id="user"),
            pytest.param(User.Role.ADMIN, "admin_add_user_to_group", id="admin"),
        ],
    )
    def test_uses_expected_payload_when_updating_role(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        role: User.Role,
        method: str,
    ) -> None:
        stubber.add_response(method, {}, group_params())
        stub_get_user(stubber, role=role)

        result = provider.update_user(id=USER_ID, update={"role": role})

        assert result.role == role

    @pytest.mark.parametrize(
        ("enabled", "method"),
        [
            pytest.param(True, "admin_enable_user", id="enable"),
            pytest.param(False, "admin_disable_user", id="disable"),
        ],
    )
    def test_uses_expected_payload_when_updating_enabled(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        enabled: bool,
        method: str,
    ) -> None:
        stubber.add_response(method, {}, user_params())
        stub_get_user(stubber, enabled=enabled)

        result = provider.update_user(id=USER_ID, update={"enabled": enabled})

        assert result.enabled is enabled

    @pytest.mark.parametrize(("code", "expected_error"), PROVIDER_ERROR_CASES)
    def test_name_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method="admin_update_user_attributes",
            code=code,
            expected_params=name_update_params(),
        )

        with pytest.raises(expected_error):
            provider.update_user(id=USER_ID, update={"name": "Alice Updated"})

    @pytest.mark.parametrize(
        ("role", "method"),
        [
            pytest.param(User.Role.USER, "admin_remove_user_from_group", id="user"),
            pytest.param(User.Role.ADMIN, "admin_add_user_to_group", id="admin"),
        ],
    )
    @pytest.mark.parametrize(("code", "expected_error"), PROVIDER_ERROR_CASES)
    def test_role_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        role: User.Role,
        method: str,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method=method,
            code=code,
            expected_params=group_params(),
        )

        with pytest.raises(expected_error):
            provider.update_user(id=USER_ID, update={"role": role})

    @pytest.mark.parametrize(
        ("enabled", "method"),
        [
            pytest.param(True, "admin_enable_user", id="enable"),
            pytest.param(False, "admin_disable_user", id="disable"),
        ],
    )
    @pytest.mark.parametrize(("code", "expected_error"), PROVIDER_ERROR_CASES)
    def test_enabled_update_maps_provider_errors(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        enabled: bool,
        method: str,
        code: str,
        expected_error: type[Exception],
    ) -> None:
        add_provider_error(
            stubber,
            method=method,
            code=code,
            expected_params=user_params(),
        )

        with pytest.raises(expected_error):
            provider.update_user(id=USER_ID, update={"enabled": enabled})


# ──── Provider Responses ─────────────────────────────────────────────────────────────


class TestResponseParsing:
    @pytest.mark.parametrize(
        "response",
        [
            pytest.param({}, id="empty-response"),
            pytest.param({"Username": USER_XID}, id="missing-required-fields"),
            pytest.param(
                {
                    "Username": USER_XID,
                    "Enabled": True,
                    "UserCreateDate": CREATED_AT,
                },
                id="missing-updated-at",
            ),
        ],
    )
    def test_rejects_unexpected_list_users_response(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
        response: dict[str, Any],
    ) -> None:
        stubber.add_response("list_users", {"Users": [response]}, list_users_params())

        with pytest.raises(DomainInvariantViolation):
            provider.list_users()

    @pytest.mark.parametrize(
        "response",
        [
            pytest.param({"Username": USER_XID}, id="missing-required-fields"),
            pytest.param(
                {
                    "Username": USER_XID,
                    "Enabled": True,
                    "UserCreateDate": CREATED_AT,
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
        stubber.add_response("admin_get_user", response, user_params())

        with pytest.raises(DomainInvariantViolation):
            provider.get_user(id=USER_ID)

    def test_normalizes_datetimes_to_utc(
        self,
        provider: user.CognitoUserProvider,
        stubber: Stubber,
    ) -> None:
        eastern = timezone(timedelta(hours=-5))
        stubber.add_response(
            "admin_get_user",
            cognito_user(
                created_at=datetime(2026, 1, 1, 7, 0, tzinfo=eastern),
                updated_at=datetime(2026, 1, 2, 8, 30, tzinfo=eastern),
                admin_get_user=True,
            ),
            user_params(),
        )
        stub_group_lookup(stubber)

        result = provider.get_user(id=USER_ID)

        assert result.created_at == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert result.updated_at == datetime(2026, 1, 2, 13, 30, tzinfo=timezone.utc)
