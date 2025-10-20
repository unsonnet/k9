# PATCH `/user/{uid}`

Update user details. Only provided fields are changed.

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

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import update.user as user -->
``user.profile``
<!-- Schema End -->

## Response 200

OK — user updated

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.user as user -->
``user.profile``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 409

Conflict — email already in use by another user (`Conflict`)

## Response 500

Internal server error (`InternalServerError`)
