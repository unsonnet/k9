import base64
import boto3
import hashlib
import hmac
import json
import os
from typing import Any

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
cognito = boto3.client("cognito-idp")


def compute_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    message = username + client_id
    digest = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


def refresh_tokens(username: str, refresh_token: str) -> dict[str, str]:
    response = cognito.initiate_auth(
        AuthFlow="REFRESH_TOKEN_AUTH",
        ClientId=CLIENT_ID,
        AuthParameters={
            "USERNAME": username,
            "REFRESH_TOKEN": refresh_token,
            "SECRET_HASH": compute_secret_hash(username, CLIENT_ID, CLIENT_SECRET),
        },
    )
    auth_result = response["AuthenticationResult"]
    return {
        "accessToken": auth_result["AccessToken"],
        "idToken": auth_result["IdToken"],
        # refreshToken is intentionally not returned
        "expiresIn": str(auth_result["ExpiresIn"]),
        "tokenType": auth_result["TokenType"],
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    def make_response(status: int, body: dict[str, Any], error: str | None = None):
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Error-Message",
            "Content-Type": "application/json",
        } | ({"Error-Message": error} if error else {})
        return {"statusCode": status, "headers": headers, "body": json.dumps(body)}

    try:
        body = json.loads(event.get("body") or "{}")
        username = body.get("username")
        refresh_token = body.get("refreshToken")
        if not username or not refresh_token:
            return make_response(400, {}, "Missing username or refresh token")
        tokens = refresh_tokens(username, refresh_token)
        return make_response(200, tokens)
    except cognito.exceptions.NotAuthorizedException:
        return make_response(401, {}, "Invalid or expired refresh token")
    except Exception as e:
        return make_response(500, {}, str(e))
