from __future__ import annotations

from tests.utils.events import make_event
from tests.utils.handlers import call_handler


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_users_admin_ok(admin_login):
    resp = call_handler(
        "user", make_event("GET", "/user", headers=_auth(admin_login["accessToken"]))
    )
    assert resp["statusCode"] == 200


def test_list_users_forbidden_user(user_login):
    resp = call_handler(
        "user", make_event("GET", "/user", headers=_auth(user_login["accessToken"]))
    )
    assert resp["statusCode"] == 403


def test_get_user_admin_ok(managed_user, admin_login):
    resp = call_handler(
        "user",
        make_event(
            "GET",
            f"/user/{managed_user['uid']}",
            headers=_auth(admin_login["accessToken"]),
        ),
    )
    assert resp["statusCode"] == 200


def test_get_user_self_ok(managed_user):
    resp = call_handler(
        "user",
        make_event(
            "GET",
            f"/user/{managed_user['uid']}",
            headers=_auth(managed_user["userToken"]),
        ),
    )
    assert resp["statusCode"] == 200


def test_get_user_forbidden_other_user(user_login, managed_user):
    resp = call_handler(
        "user",
        make_event(
            "GET",
            f"/user/{managed_user['uid']}",
            headers=_auth(user_login["accessToken"]),
        ),
    )
    assert resp["statusCode"] == 403


def test_update_user_admin_ok(managed_user, admin_login):
    resp = call_handler(
        "user",
        make_event(
            "PATCH",
            f"/user/{managed_user['uid']}",
            headers=_auth(admin_login["accessToken"]),
            body={"name": "Updated"},
        ),
    )
    assert resp["statusCode"] == 200


def test_update_user_self_ok(managed_user):
    resp = call_handler(
        "user",
        make_event(
            "PATCH",
            f"/user/{managed_user['uid']}",
            headers=_auth(managed_user["userToken"]),
            body={"name": "Self Updated"},
        ),
    )
    assert resp["statusCode"] == 200


def test_update_user_forbidden_not_self_not_admin(user_login, managed_user):
    resp = call_handler(
        "user",
        make_event(
            "PATCH",
            f"/user/{managed_user['uid']}",
            headers=_auth(user_login["accessToken"]),
            body={"name": "Nope"},
        ),
    )
    assert resp["statusCode"] == 403


def test_update_password_admin_ok(managed_user, admin_login):
    resp = call_handler(
        "user",
        make_event(
            "PATCH",
            f"/user/{managed_user['uid']}/password",
            headers=_auth(admin_login["accessToken"]),
            body={"newPassword": "BetterPW1!"},
        ),
    )
    assert resp["statusCode"] == 204


def test_update_password_self_requires_current(managed_user):
    resp = call_handler(
        "user",
        make_event(
            "PATCH",
            f"/user/{managed_user['uid']}/password",
            headers=_auth(managed_user["userToken"]),
            body={"newPassword": "NewBetterPW1!"},
        ),
    )
    assert resp["statusCode"] == 403


def test_delete_user_forbidden_non_admin(user_login, managed_user):
    resp = call_handler(
        "user",
        make_event(
            "DELETE",
            f"/user/{managed_user['uid']}",
            headers=_auth(user_login["accessToken"]),
        ),
    )
    assert resp["statusCode"] == 403


def test_delete_user_admin_ok(managed_user, admin_login):
    resp = call_handler(
        "user",
        make_event(
            "DELETE",
            f"/user/{managed_user['uid']}",
            headers=_auth(admin_login["accessToken"]),
        ),
    )
    assert resp["statusCode"] == 204
