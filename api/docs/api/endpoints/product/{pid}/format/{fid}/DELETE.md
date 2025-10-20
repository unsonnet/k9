# DELETE `/product/{pid}/format/{fid}`

Delete product format. Operation is irreversible.

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

## Response 204

No content — format deleted

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — product or format does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
