# POST `/auth/login`

Authenticate user with username and password.

## Request

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.credentials``
<!-- Schema End -->

## Response 200

OK — user logged in

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.session``
<!-- Schema End -->

## Response 202

Accepted — new password required

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.challenge``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — invalid credentials (`Unauthorized`)

## Response 403

Forbidden — user not confirmed (`UserNotConfirmed`)

## Response 404

Not found — user does not exist (`UserNotFound`)

## Response 500

Internal server error (`InternalServerError`)
