# PATCH `/product/{pid}/format/{fid}`

Update product format. Dimensions are replaced, not merged.
Only provided fields are changed.

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
<!-- import update.product as product -->
``product.format``
<!-- Schema End -->

## Response 200

OK - format updated

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.format``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload or aspect mismatch (`InvalidRequest`, `MismatchedShape`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — product or format does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
