from __future__ import annotations

from tests.utils.events import make_event, parse_body
from tests.utils.handlers import call_handler


def force_user_established(username: str, temp_password: str) -> dict[str, str]:
    """
    Perform the NEW_PASSWORD_REQUIRED flow for a newly created user:
      1) login w/ temp password → 202
      2) POST /auth/reset → 204
      3) login w/ new password → 200
    Returns:
      { "user": <UUID>, "token": <accessToken>, "username": <username> }
    """
    # Step 1: First login must trigger challenge
    first = call_handler(
        "auth",
        make_event(
            "POST",
            "/auth/login",
            body={"username": username, "password": temp_password},
        ),
    )
    assert first["statusCode"] == 202, f"Expected challenge login for new user: {first}"
    chal = parse_body(first)
    session = chal["session"]

    # Step 2: Reset password to a stable known good one
    new_pw = "TestPW1!"
    reset = call_handler(
        "auth",
        make_event(
            "POST",
            "/auth/reset",
            body={"username": username, "session": session, "newPassword": new_pw},
        ),
    )
    assert reset["statusCode"] == 204, f"Reset failed: {reset}"

    # Step 3: Login again, now must succeed
    final = call_handler(
        "auth",
        make_event(
            "POST", "/auth/login", body={"username": username, "password": new_pw}
        ),
    )
    assert final["statusCode"] == 200, f"Final login failed: {final}"
    body = parse_body(final)

    return {"user": body["user"], "token": body["accessToken"], "username": username}
