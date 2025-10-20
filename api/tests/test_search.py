import json

from src.app import lambda_handler


def test_search_empty_returns_no_results(auth_header_user, make_event):
    body = {}
    res = lambda_handler(make_event("/search", "POST", headers=auth_header_user, body=body, query={"limit": "10"}), None)
    assert res["statusCode"] == 200
    payload = json.loads(res["body"])
    assert payload["total"] == 0
    assert isinstance(payload["results"], list)


def test_search_with_filters(auth_header_user, make_event):
    body = {
        "name": {"brand": "Acme"},
        "category": {"type": ["tile"]},
        "format": {"aspect": "600:300", "length": {"min": 500, "max": 700, "unit": "mm"}},
        "vendor": {"store": ["A"], "discontinued": False, "price": {"min": 0, "max": 10000, "unit": "USD"}},
    }
    res = lambda_handler(make_event("/search", "POST", headers=auth_header_user, body=body, query={"limit": "5", "partial": "true"}), None)
    assert res["statusCode"] == 200
    payload = json.loads(res["body"])
    assert payload["total"] >= 0
