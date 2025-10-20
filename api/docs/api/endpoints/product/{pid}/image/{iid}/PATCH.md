# PATCH `/product/{pid}/image/{iid}`

Update image metadata (mask and homography matrix).
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
| iid | `string` | required | Image ID (`UUID`) |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import update.product as product -->
``product.image``
<!-- Schema End -->

## Response 200

OK - image updated

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.image``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload or image metadata (`InvalidRequest`, `InvalidBooleanMask`, `InvalidHomography`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — product or image does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)