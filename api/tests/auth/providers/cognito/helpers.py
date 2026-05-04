def auth_params(provider, *, username="alice", password="secret"):
    return {
        "ClientId": "client-id",
        "AuthFlow": "USER_PASSWORD_AUTH",
        "AuthParameters": {
            "SECRET_HASH": provider._secret_hash(username),
            "USERNAME": username,
            "PASSWORD": password,
        },
    }


def token_response(
    *,
    access_token="access-token",
    expires_in=3600,
    refresh_token="refresh-token",
    id_token="id-token",
):
    return {
        "AuthenticationResult": {
            "AccessToken": access_token,
            "ExpiresIn": expires_in,
            "RefreshToken": refresh_token,
            "IdToken": id_token,
        }
    }


def expected_tokens(
    *,
    access_token="access-token",
    expires_in=3600,
    refresh_token="refresh-token",
    id_token="id-token",
):
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "id_token": id_token,
    }
