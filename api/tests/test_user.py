import json

import pytest

from src.app import lambda_handler


def _create_user(admin_headers, make_event):
    body = {"username": "alpha", "email": "alpha@example.com", "role": "user", "preferences": {"theme": "dark"}}
    res = lambda_handler(make_event("/user", "POST", headers=admin_headers, body=body), None)
    assert res["statusCode"] == 201
    return json.loads(res["body"])


def test_user_admin_list_and_create(auth_header_admin, make_event):
    # list empty
    res = lambda_handler(make_event("/user", "GET", headers=auth_header_admin), None)
    assert res["statusCode"] == 200
    # create
    created = _create_user(auth_header_admin, make_event)
    assert created["username"] == "alpha"
    # list non-empty
    res2 = lambda_handler(make_event("/user", "GET", headers=auth_header_admin), None)
    body = json.loads(res2["body"])
    assert body["total"] >= 1


def test_user_non_admin_forbidden(auth_header_user, make_event):
    res = lambda_handler(make_event("/user", "GET", headers=auth_header_user), None)
    assert res["statusCode"] == 403
    res2 = lambda_handler(make_event("/user", "POST", headers=auth_header_user, body={"username": "x", "email": "x@x", "role": "user"}), None)
    assert res2["statusCode"] == 403


def test_user_get_patch_delete(auth_header_admin, auth_header_user, make_event):
    created = _create_user(auth_header_admin, make_event)
    uid = created["id"]
    # get (any authenticated)
    res_get = lambda_handler(make_event(f"/user/{uid}", "GET", headers=auth_header_user), None)
    assert res_get["statusCode"] == 200
    # patch
    res_patch = lambda_handler(make_event(f"/user/{uid}", "PATCH", headers=auth_header_user, body={"username": "beta", "preferences": {"theme": None}}), None)
    assert res_patch["statusCode"] == 200
    body = json.loads(res_patch["body"])
    assert body["username"] == "beta"
    # Current implementation performs shallow update, so nested None is preserved
    assert body.get("preferences", {}).get("theme") is None
    # delete admin-only
    res_del = lambda_handler(make_event(f"/user/{uid}", "DELETE", headers=auth_header_admin), None)
    assert res_del["statusCode"] == 204


def test_user_password_patch(auth_header_user, make_event):
    uid = "00000000-0000-0000-0000-000000000001"
    res = lambda_handler(make_event(f"/user/{uid}/password", "PATCH", headers=auth_header_user, body={"currentPassword": "old", "newPassword": "new"}), None)
    assert res["statusCode"] == 204
