# K9 API Test Suite

This directory contains end-to-end tests for the Lambda-style API handlers defined under `src/handlers/*` and routed by `src/app.py`.

What is covered:
- Auth: `/auth/login`, `/auth/refresh`, `/auth/forgot`, `/auth/reset`, `/auth/logout`
- Users: `/user` list/create (admin only), `/user/{uid}` get/patch/delete, `/user/{uid}/password` patch
- Products: `/product` create, `/product/{pid}` get/patch/delete
  - Formats: `/product/{pid}/format` create, `/product/{pid}/format/{fid}` patch/delete
  - Vendors: `/product/{pid}/format/{fid}/vendor` create, `/product/{pid}/format/{fid}/vendor/{vid}` patch/delete
  - Images: `/product/{pid}/image` create (JSON with base64), `/product/{pid}/image/{iid}` patch/delete
- Reports: `/report` list/create, `/report/{rid}` get/patch/delete, `/report/{rid}/favorite/{pid}` put/delete
- Search: `/search` post with filters and pagination query params

How tests run:
- Tests construct API Gateway–like events and call `src.app.lambda_handler` directly.
- Repositories and image storage use an in-memory store automatically during pytest runs.
- JWTs are generated locally with the configured `JWT_SECRET` and validated by the app.

Prereqs:
- Python 3.9–3.12
- Dependencies installed (using uv or pip)

Run in VS Code (no terminal required):
- Open the Testing side bar (beaker icon).
- Click Refresh to discover tests under `tests/`.
- Use Run All Tests or run by file/test. You can also debug individual tests.

Optional terminal run:
```bash
# from repo root or the api folder
uv sync  # or: pip install -e .[dev]
pytest -q
```

Troubleshooting:
- If Pillow is missing, ensure dependencies are installed; the image tests require it.
- If authorization errors occur, ensure no conflicting `AUTH_MODE` env var is set (tests assume local JWT mode).
- If using a different test runner, keep `PYTEST_CURRENT_TEST` semantics to allow in-memory repositories.
