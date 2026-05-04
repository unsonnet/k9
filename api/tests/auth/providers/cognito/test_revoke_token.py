import pytest
from botocore.stub import Stubber
from shared.errors import DomainInvariantViolation

pytestmark = pytest.mark.unit


def test_with_access_token_uses_global_sign_out(provider, cognito_client):
    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "global_sign_out",
            {},
            {"AccessToken": "access-token"},
        )

        provider.revoke_tokens(access_token="access-token")


def test_with_refresh_token_uses_revoke_token(provider, cognito_client):
    expected_params = {
        "ClientId": "client-id",
        "ClientSecret": "client-secret-value-1234",
        "Token": "refresh-token",
    }

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "revoke_token",
            {},
            expected_params,
        )

        provider.revoke_tokens(refresh_token="refresh-token")


def test_requires_exactly_one_token(provider):
    with pytest.raises(DomainInvariantViolation):
        provider.revoke_tokens()

    with pytest.raises(DomainInvariantViolation):
        provider.revoke_tokens(
            access_token="access-token",
            refresh_token="refresh-token",
        )
