# POST `/report`

Create report.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import create.report as report -->
``report.report``
<!-- Schema End -->

## Response 201

Created — report created

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.report as report -->
``report.report``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — referenced product does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)