# POST `/product/{pid}/image`

Upload product image with mask and homography for normalization.

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

### Body (`multipart/form-data`)

<!-- Schema Begin -->
<!-- import create.product as product -->
``product.image``
<!-- Schema End -->

## Response 201

Created — image created

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.product as product -->
``product.image``
<!-- Schema End -->

## Response 400

Bad request — invalid image data or homography (`InvalidImageFormat`, `InvalidHomography`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — product does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)