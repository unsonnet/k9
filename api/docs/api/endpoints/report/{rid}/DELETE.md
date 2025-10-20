# DELETE `/report/{rid}`

Delete report and associated data. Operation is irreversible.

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
| rid | `string` | required | Report ID (`UUID`) |
<!-- Schema End -->

## Response 200

OK — report deleted

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — report does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
