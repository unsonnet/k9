from src.app import lambda_handler


def test_login_smoke():
    event = {
        "rawPath": "/auth/login",
        "requestContext": {"http": {"method": "POST"}},
        "body": '{"email":"user@example.com","password":"secret"}',
    }
    resp = lambda_handler(event, None)
    assert resp["statusCode"] == 200


def test_product_create_get_flow():
    # login to get a token
    event = {
        "rawPath": "/auth/login",
        "requestContext": {"http": {"method": "POST"}},
        "body": '{"email":"user@example.com","password":"secret"}',
    }
    login = lambda_handler(event, None)
    token = __import__("json").loads(login["body"]).get("accessToken")

    # create product
    body = {
        "name": {"brand": "Acme", "series": "X", "model": "100"},
        "category": {"type": "tile"},
    }
    event = {
        "rawPath": "/product",
        "requestContext": {"http": {"method": "POST"}},
        "headers": {"Authorization": f"Bearer {token}"},
        "body": __import__("json").dumps(body),
    }
    created = lambda_handler(event, None)
    assert created["statusCode"] == 201

