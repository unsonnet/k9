# GET `/user/{uid}`

Retrieve user by ID.

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

## Response 200

OK — user retrieved

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.user as user -->
``user.profile``
<!-- Schema End -->

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
