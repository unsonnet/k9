# POST `/auth/forgot`

Request password reset for user account.

## Request

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.forgot``
<!-- Schema End -->

## Response 204

No content — password reset email sent

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 404

Not found — user with email does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
