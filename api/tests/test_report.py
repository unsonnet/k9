import json

from src.app import lambda_handler


def _ensure_product(auth_header_user, make_event) -> str:
    body = {"name": {"brand": "R", "series": "S", "model": "M"}, "category": {"type": "tile"}}
    res = lambda_handler(make_event("/product", "POST", headers=auth_header_user, body=body), None)
    assert res["statusCode"] == 201
    return json.loads(res["body"])['id']


def test_report_flow(auth_header_user, make_event):
    # list initial
    res_list = lambda_handler(make_event("/report", "GET", headers=auth_header_user), None)
    assert res_list["statusCode"] == 200
    # create
    pid = _ensure_product(auth_header_user, make_event)
    res_create = lambda_handler(make_event("/report", "POST", headers=auth_header_user, body={"title": "T", "reference": pid}), None)
    assert res_create["statusCode"] == 201
    report = json.loads(res_create["body"])
    rid = report["id"]
    # get
    res_get = lambda_handler(make_event(f"/report/{rid}", "GET", headers=auth_header_user), None)
    assert res_get["statusCode"] == 200
    # patch change title
    res_patch = lambda_handler(make_event(f"/report/{rid}", "PATCH", headers=auth_header_user, body={"title": "T2"}), None)
    assert res_patch["statusCode"] == 200
    # favorite add and remove
    res_fav_add = lambda_handler(make_event(f"/report/{rid}/favorite/{pid}", "PUT", headers=auth_header_user), None)
    assert res_fav_add["statusCode"] == 204
    res_fav_del = lambda_handler(make_event(f"/report/{rid}/favorite/{pid}", "DELETE", headers=auth_header_user), None)
    assert res_fav_del["statusCode"] == 204
    # delete
    res_del = lambda_handler(make_event(f"/report/{rid}", "DELETE", headers=auth_header_user), None)
    assert res_del["statusCode"] == 204
