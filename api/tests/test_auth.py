import json

from src.app import lambda_handler


def test_auth_login_success(make_event):
    evt = make_event("/auth/login", "POST", body={"username": "user1", "password": "secret"})
    res = lambda_handler(evt, None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert set(body.keys()) == {"user", "accessToken", "refreshToken", "expiresIn"}


def test_auth_login_missing_fields(make_event):
    evt = make_event("/auth/login", "POST", body={"username": "", "password": ""})
    res = lambda_handler(evt, None)
    assert res["statusCode"] == 401


def test_auth_refresh_flow(make_event):
    login = lambda_handler(make_event("/auth/login", "POST", body={"username": "alice", "password": "p"}), None)
    refresh_token = json.loads(login["body"])['refreshToken']
    res = lambda_handler(make_event("/auth/refresh", "POST", body={"username": "alice", "refreshToken": refresh_token}), None)
    assert res["statusCode"] == 200
    body = json.loads(res["body"])
    assert body["accessToken"] and body["refreshToken"]


def test_auth_forgot_and_reset(make_event):
    res = lambda_handler(make_event("/auth/forgot", "POST", body={"username": "user1"}), None)
    assert res["statusCode"] == 204
    # reset requires fields
    res2 = lambda_handler(make_event("/auth/reset", "POST", body={"username": "user1", "session": "s", "newPassword": "x"}), None)
    assert res2["statusCode"] == 204


def test_auth_logout(make_event, auth_header_user):
    res = lambda_handler(make_event("/auth/logout", "POST", headers=auth_header_user), None)
    assert res["statusCode"] == 204
