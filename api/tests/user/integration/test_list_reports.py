import pytest
from shared.errors import DomainNotFound, DomainRateLimited
from user.providers.report import ReportPage

from .conftest import make_report

pytestmark = pytest.mark.integration


def test_user_lists_own_reports_with_me(
    user_handler_module,
    dummy_report_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, user_caller)
    dummy_report_provider.list_result = ReportPage(
        reports=[
            make_report(
                id="report-1",
                user="user-1",
                title="Report One",
                final=True,
            )
        ],
        cursor="next-cursor",
    )

    response = user_handler_module.lambda_handler(
        apigw_event(
            "/user/me/reports",
            method="GET",
            query_params={
                "q": "report",
                "final": "true",
                "dateFrom": "2026-01-01",
                "dateTo": "2026-01-31",
                "limit": 10,
                "cursor": "cursor-1",
            },
        ),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_report_provider.list_calls == [
        {
            "user": "user-1",
            "q": "report",
            "final": "true",
            "date_from": "2026-01-01",
            "date_to": "2026-01-31",
            "limit": 10,
            "cursor": "cursor-1",
        }
    ]

    body = response_body(response)
    assert body["cursor"] == "next-cursor"
    assert body["reports"][0]["id"] == "report-1"
    assert body["reports"][0]["user"] == "user-1"
    assert body["reports"][0]["title"] == "Report One"
    assert body["reports"][0]["final"] is True


def test_user_lists_own_reports_by_id(
    user_handler_module,
    dummy_report_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, user_caller)
    dummy_report_provider.list_result = ReportPage(reports=[], cursor=None)

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-1/reports", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_report_provider.list_calls[0]["user"] == "user-1"


def test_user_cannot_list_another_users_reports(
    user_handler_module,
    dummy_report_provider,
    user_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, user_caller)

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-2/reports", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 403
    assert response_body(response)["title"] == "Forbidden"
    assert dummy_report_provider.list_calls == []


def test_admin_lists_another_users_reports(
    user_handler_module,
    dummy_report_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
):
    use_caller(user_handler_module, admin_caller)
    dummy_report_provider.list_result = ReportPage(
        reports=[make_report(id="report-2", user="user-2", title="Report Two")],
        cursor=None,
    )

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-2/reports", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 200
    assert dummy_report_provider.list_calls[0]["user"] == "user-2"


def test_list_reports_maps_not_found_to_404(
    user_handler_module,
    dummy_report_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_report_provider.list_error = DomainNotFound("User not found")

    response = user_handler_module.lambda_handler(
        apigw_event("/user/missing-user/reports", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 404
    assert response_body(response)["title"] == "Not Found"


def test_list_reports_maps_rate_limit_to_429(
    user_handler_module,
    dummy_report_provider,
    admin_caller,
    use_caller,
    apigw_event,
    lambda_context,
    response_body,
):
    use_caller(user_handler_module, admin_caller)
    dummy_report_provider.list_error = DomainRateLimited()

    response = user_handler_module.lambda_handler(
        apigw_event("/user/user-1/reports", method="GET"),
        lambda_context,
    )

    assert response["statusCode"] == 429
    assert response_body(response)["title"] == "Too Many Requests"
