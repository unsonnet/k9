from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    assert_unreachable,
)
from shared.http import Body, HttpResolver, Path, Query
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK

from .providers.report import ReportProvider
from .providers.user import UserProvider
from .service import UserRequest, UserResponse, UserService

app = HttpResolver(enable_validation=True)
svc = UserService(UserProvider(), ReportProvider())  # type: ignore[reportAbstractUsage]


@app.get(
    "/user",
    summary="List users",
    description="List or search users. Requires admin role.",
    tags=["user"],
    responses={
        200: "Users found",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def list_users(
    q: Query[str | None] = None,
    limit: Query[int | None] = None,
    cursor: Query[str | None] = None,
) -> OK[UserResponse.UserPage] | Unauthorized | Forbidden | TooManyRequests:
    request = UserRequest.ListUsers(q=q, limit=limit, cursor=cursor)
    try:
        match svc.list_users(app.caller(), request):
            case UserResponse.UserPage() as page:
                return OK(page)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/user/<userId>",
    summary="Read user profile",
    description=(
        "Read a user profile. The special userId value 'me' resolves to the "
        "authenticated caller. Reading another user's profile requires admin role."
    ),
    tags=["user"],
    responses={
        200: "User found",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def get_user(
    userId: Path[str],
) -> OK[UserResponse.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    request = UserRequest.GetUser(id=userId)
    try:
        match svc.get_user(app.caller(), request):
            case UserResponse.User() as user:
                return OK(user)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/user/<userId>",
    summary="Update user profile",
    description=(
        "Update a user profile. The special userId value 'me' resolves to the "
        "authenticated caller. Updating another user's profile requires admin role."
    ),
    tags=["user"],
    responses={
        200: "User updated",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def update_user(
    userId: Path[str],
    update: Body[UserRequest.UpdateUser.Update],
) -> OK[UserResponse.User] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    request = UserRequest.UpdateUser(id=userId, update=update)
    try:
        match svc.update_user(app.caller(), request):
            case UserResponse.User() as user:
                return OK(user)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/user/<userId>/reports",
    summary="List user reports",
    description=(
        "List or search reports associated with a user. The special userId value 'me' "
        "resolves to the authenticated caller. Listing another user's reports requires "
        "admin role."
    ),
    tags=["user"],
    responses={
        200: "Reports found",
        401: "Authentication required",
        403: "Access denied",
        404: "User not found",
        429: "Too many requests",
    },
)
def list_reports(
    userId: Path[str],
    q: Query[str | None] = None,
    final: Query[str | None] = None,
    dateFrom: Query[str | None] = None,
    dateTo: Query[str | None] = None,
    limit: Query[int | None] = None,
    cursor: Query[str | None] = None,
) -> (
    OK[UserResponse.ReportPage] | Unauthorized | Forbidden | NotFound | TooManyRequests
):
    request = UserRequest.ListReports(
        user=userId,
        q=q,
        final=final,
        dateFrom=dateFrom,
        dateTo=dateTo,
        limit=limit,
        cursor=cursor,
    )
    try:
        match svc.list_reports(app.caller(), request):
            case UserResponse.ReportPage() as page:
                return OK(page)
            case _ as never:
                assert_unreachable(never)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
