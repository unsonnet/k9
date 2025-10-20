# GET `/product/{pid}`

Retrieve product by ID.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Path Parameters

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| pid | `string` | required | Product ID (`UUID`) |
<!-- Schema End -->

## Response 200

OK - product retrieved

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.product``
<!-- Schema End -->

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — product does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)