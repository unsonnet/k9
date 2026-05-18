# Running tests in this workspace

Use the VS Code test runner tool with workspace-relative paths.

## Correct patterns

- Run one file: files=["tests/user/integration/test_validation.py"]
- Run specific tests in a file: files=["tests/user/integration/test_validation.py"], testNames=["test_list_users_rejects_invalid_limit"]
- Run multiple files: files=["tests/user/integration/test_get_user.py", "tests/user/integration/test_list_users.py"]

## Important gotchas

- Do not pass pytest node ids in files (example: path::test_name). It will report "No tests found".
- Absolute file paths can be inconsistent with this runner in this repo; prefer workspace-relative paths under tests/.

## Quick fallback

If the test runner tool behaves unexpectedly, use terminal pytest from workspace root:

uv run python -m pytest tests/user/integration -q
