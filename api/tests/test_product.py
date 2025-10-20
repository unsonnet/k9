import base64
import json

import pytest

from src.app import lambda_handler


def test_product_crud(create_product, auth_header_user, make_event):
    created = create_product()
    pid = created["id"]
    # get
    res_get = lambda_handler(make_event(f"/product/{pid}", "GET", headers=auth_header_user), None)
    assert res_get["statusCode"] == 200
    # patch name and category removal
    patch_body = {"name": {"brand": "Acme2", "series": None}, "category": {"material": None}}
    res_patch = lambda_handler(make_event(f"/product/{pid}", "PATCH", headers=auth_header_user, body=patch_body), None)
    assert res_patch["statusCode"] == 200
    obj = json.loads(res_patch["body"])
    assert obj["name"]["brand"] == "Acme2"
    assert "series" not in obj["name"]
    assert "material" not in obj["category"]
    # delete
    res_del = lambda_handler(make_event(f"/product/{pid}", "DELETE", headers=auth_header_user), None)
    assert res_del["statusCode"] == 204


def test_product_formats_and_vendors(create_product, auth_header_user, make_event):
    product = create_product()
    pid = product["id"]
    # create format
    fmt_body = {"aspect": "600:300", "length": {"value": 600, "unit": "mm"}, "width": {"value": 300, "unit": "mm"}}
    res_fmt = lambda_handler(make_event(f"/product/{pid}/format", "POST", headers=auth_header_user, body=fmt_body), None)
    assert res_fmt["statusCode"] == 201
    fmt = json.loads(res_fmt["body"])
    fid = fmt["id"]
    # update format remove thickness
    res_fmt_upd = lambda_handler(make_event(f"/product/{pid}/format/{fid}", "PATCH", headers=auth_header_user, body={"thickness": None}), None)
    assert res_fmt_upd["statusCode"] == 200
    fmt2 = json.loads(res_fmt_upd["body"])
    assert "thickness" not in fmt2
    # vendor create
    ven_body = {"sku": "SKU1", "store": "StoreA", "name": "VendorA", "price": {"value": 1000, "unit": "USD"}}
    res_ven = lambda_handler(make_event(f"/product/{pid}/format/{fid}/vendor", "POST", headers=auth_header_user, body=ven_body), None)
    assert res_ven["statusCode"] == 201
    ven = json.loads(res_ven["body"])
    vid = ven["id"]
    # vendor patch discontinue and remove url
    res_ven_upd = lambda_handler(make_event(f"/product/{pid}/format/{fid}/vendor/{vid}", "PATCH", headers=auth_header_user, body={"discontinued": True, "url": None}), None)
    assert res_ven_upd["statusCode"] == 200
    # vendor delete
    res_ven_del = lambda_handler(make_event(f"/product/{pid}/format/{fid}/vendor/{vid}", "DELETE", headers=auth_header_user), None)
    assert res_ven_del["statusCode"] == 204
    # delete format
    res_fmt_del = lambda_handler(make_event(f"/product/{pid}/format/{fid}", "DELETE", headers=auth_header_user), None)
    assert res_fmt_del["statusCode"] == 204


def test_product_images_flow(create_product, auth_header_user, make_event, png_base64):
    product = create_product()
    pid = product["id"]
    # create image with JSON base64
    payload = {"image": png_base64(2), "mask": base64.b64encode(b"mask").decode(), "hom": base64.b64encode(b"hom").decode()}
    res_img = lambda_handler(make_event(f"/product/{pid}/image", "POST", headers=auth_header_user, body=payload), None)
    assert res_img["statusCode"] == 201
    img = json.loads(res_img["body"])
    iid = img["id"]
    # patch image metadata noop
    res_img_upd = lambda_handler(make_event(f"/product/{pid}/image/{iid}", "PATCH", headers=auth_header_user, body={"mask": base64.b64encode(b"m").decode()}), None)
    assert res_img_upd["statusCode"] == 200
    # delete image
    res_img_del = lambda_handler(make_event(f"/product/{pid}/image/{iid}", "DELETE", headers=auth_header_user), None)
    assert res_img_del["statusCode"] == 204
