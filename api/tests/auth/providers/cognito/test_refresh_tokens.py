import pytest
from auth.providers.auth import Tokens
from botocore.stub import Stubber

from .helpers import token_response

pytestmark = pytest.mark.unit


def test_uses_expected_payload_and_returns_tokens(provider, cognito_client):
    expected_params = {
        "ClientId": "client-id",
        "ClientSecret": "client-secret-value-1234",
        "RefreshToken": "refresh-token",
    }

    response = token_response(
        access_token="new-access-token",
        refresh_token="refresh-token",
        id_token="new-id-token",
    )

    with Stubber(cognito_client) as stubber:
        stubber.add_response(
            "get_tokens_from_refresh_token",
            response,
            expected_params,
        )

        result = provider.refresh_tokens(refresh_token="refresh-token")

    assert result == Tokens(
        access_token="new-access-token",
        expires_in=3600,
        refresh_token="refresh-token",
        id_token="new-id-token",
    )
