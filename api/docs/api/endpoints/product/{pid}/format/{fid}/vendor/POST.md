# POST `/product/{pid}/format/{fid}/vendor`

Create product format vendor listing.

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
| fid | `string` | required | Format ID (`UUID`) |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import create.product as product -->
``product.vendor``
<!-- Schema End -->

## Response 200

OK - vendor created

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.vendor``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 404

Not found — product or format does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
