# POST `/product`

Create product.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import create.product as product -->
``product.product``
<!-- Schema End -->

## Response 200

OK - product created

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.product``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 500

Internal server error (`InternalServerError`)