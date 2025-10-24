import base64
import boto3
import hashlib
import hmac
import json
import os
from time import sleep
from typing import Any

USER_POOL_ID = os.environ["USER_POOL_ID"]
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


def logout_other_devices(username: str) -> None:
    cognito.admin_user_global_sign_out(
        UserPoolId=USER_POOL_ID,
        Username=username,
    )
    sleep(1)  # attempt to avoid race condition


def login_user(username: str, password: str) -> dict[str, str]:
    logout_other_devices(username)
    response = cognito.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        ClientId=CLIENT_ID,
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password,
            "SECRET_HASH": compute_secret_hash(username, CLIENT_ID, CLIENT_SECRET),
        },
    )
    if response.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
        return {
            "challenge": "NEW_PASSWORD_REQUIRED",
            "session": response["Session"],
            "username": username,
        }
    auth_result = response["AuthenticationResult"]
    return {
        "accessToken": auth_result["AccessToken"],
        "idToken": auth_result["IdToken"],
        "refreshToken": auth_result["RefreshToken"],
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
        password = body.get("password")
        if not username or not password:
            return make_response(400, {}, "Missing username or password")
        response = login_user(username, password)
        status = 202 if "challenge" in response else 200
        return make_response(status, response)
    except cognito.exceptions.NotAuthorizedException:
        return make_response(401, {}, "Invalid username or password")
    except cognito.exceptions.UserNotConfirmedException:
        return make_response(403, {}, "User not confirmed")
    except cognito.exceptions.UserNotFoundException:
        return make_response(404, {}, "User not confirmed")
    except Exception as e:
        return make_response(500, {}, str(e))
