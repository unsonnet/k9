# DELETE `/user/{uid}`

Delete a user account.
Only for administrator role.

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
| uid | `string` | required | User ID (`UUID`) |
<!-- Schema End -->

## Response 204

No content — user deleted

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
