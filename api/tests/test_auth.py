import json

from src.app import lambda_handler


def test_auth_login_success(make_event):
    evt = make_event("/auth/login", "POST", body={"email": "user@example.com", "password": "secret"})
    res = lambda_handler(evt, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert set(body.keys()) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_auth_login_missing_fields(make_event):
    evt = make_event("/auth/login", "POST", body={"email": "", "password": ""})
    res = lambda_handler(evt, None)
    assert res["statusCode"] == 401


def test_auth_refresh_flow(make_event):
    login = lambda_handler(make_event("/auth/login", "POST", body={"email": "a@b.com", "password": "p"}), None)
    refresh_token = json.loads(login["body"])['refreshToken']
    res = lambda_handler(make_event("/auth/refresh", "POST", body={"refreshToken": refresh_token}), None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["accessToken"] and body["refreshToken"]


def test_auth_forgot_and_reset(make_event):
    res = lambda_handler(make_event("/auth/forgot", "POST", body={"email": "user@example.com"}), None)
    assert res["statusCode"] == 204
    # reset requires fields
    res2 = lambda_handler(make_event("/auth/reset", "POST", body={"user": "00000000-0000-0000-0000-000000000001", "session": "s", "newPassword": "x"}), None)
    assert res2["statusCode"] == 204


def test_auth_logout(make_event):
    res = lambda_handler(make_event("/auth/logout", "POST"), None)
    assert res["statusCode"] == 204
