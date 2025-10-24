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


def respond_new_password(username: str, new_password: str, session: str) -> None:
    cognito.respond_to_auth_challenge(
        ClientId=CLIENT_ID,
        ChallengeName="NEW_PASSWORD_REQUIRED",
        ChallengeResponses={
            "USERNAME": username,
            "NEW_PASSWORD": new_password,
            "SECRET_HASH": compute_secret_hash(username, CLIENT_ID, CLIENT_SECRET),
        },
        Session=session,
    )


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
        new_password = body.get("newPassword")
        session = body.get("session")
        if not all([username, new_password, session]):
            return make_response(400, {}, "Missing username, new password, or session")
        respond_new_password(username, new_password, session)
        return make_response(200, {"success": True})
    except cognito.exceptions.NotAuthorizedException:
        return make_response(401, {}, "Invalid credentials")
    except cognito.exceptions.ExpiredCodeException:
        return make_response(410, {}, "Session expired")
    except Exception as e:
        return make_response(500, {}, str(e))
