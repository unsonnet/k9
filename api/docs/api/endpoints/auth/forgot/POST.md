# POST `/auth/forget`

Request password reset for user account.

## Request

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.forget``
<!-- Schema End -->

## Response 204

No content — password reset link sent to admin

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
