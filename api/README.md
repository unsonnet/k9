# K9 API — Serverless Backend

K9 API is a Python serverless backend that exposes REST endpoints for auth, users, products, reports, and search. It runs on AWS Lambda behind an API Gateway HTTP API, with DynamoDB and S3 as data stores and optional OpenSearch for search queries.

Docs: see `api.md` (full reference) or open `docs/api.html`.

## What’s inside

- Runtime: Python 3.11 on AWS Lambda (AWS SAM)
- API Gateway HTTP API → single Lambda handler (`src/app.py`)
- Data:
  - DynamoDB tables: products, users, reports (with GSI on `author`)
  - S3 bucket for normalized product images
  - Optional OpenSearch endpoint for search
- Auth: local JWT (HS256) by default; Cognito (RS256) optional
- Packaging: Lambda Layers for dependencies (requirements in `requirements/*.txt`)
- Tests: pytest in `tests/`

Key files:
- `template.yaml` — AWS SAM template (all AWS resources + Lambda env)
- `src/app.py` — request router (auth/product/report/search/user)
- `src/config.py` — configuration via environment variables
- `scripts/build.sh` — builds Lambda layers from `requirements/`
- `scripts/dev.sh` — builds and runs the API locally via `sam local start-api`
- `scripts/deploy.sh` — builds and deploys to AWS via `sam deploy`

## Repository layout

- `src/` — app source
  - `handlers/` — per-domain request routing
  - `services/` — data access and business logic
  - `models/` — API and domain models
  - `utils/` — helpers (HTTP responses, auth utils, etc.)
- `docs/` — generated endpoint docs (see `api.html` and Markdown under `docs/api/`)
- `requirements/` — layer requirements (`core.txt`, `data.txt`, `ml.txt`)
- `tests/` — unit tests

## Prerequisites

- Linux/macOS with bash
- Python 3.11 (required for Lambda layers and local tooling)
- Docker (for `sam local`, to emulate Lambda)
- AWS CLI v2 (configured credentials with permissions for CloudFormation, Lambda, API Gateway, DynamoDB, S3)
- AWS SAM CLI (build, local, deploy)
- Recommended: `uv` for fast Python dependency management

## Local development

You can run the API locally with AWS SAM. The script will build layers and start a local HTTP server.

1) Build and start the local API (port 3001):

```bash
./scripts/dev.sh
```

- Visit http://127.0.0.1:3001 to call endpoints (see routes in `api.md`).
- To change the port: `./scripts/dev.sh -p 8080`
- By default, `OpenSearchEndpoint` parameter is empty. If you have an OpenSearch endpoint for local testing, start SAM with parameter overrides:

```bash
# Optional: run SAM directly with parameters
sam build --template-file template.yaml
sam local start-api \
  --template-file template.yaml \
  --parameter-overrides OpenSearchEndpoint="https://your-opensearch.example.com"
```

Environment variables used at runtime (defaults in `src/config.py`):
- `AWS_REGION` / `AWS_DEFAULT_REGION` (default `us-east-1`)
- `PRODUCTS_TABLE` (default `k9_products`)
- `USERS_TABLE` (default `k9_users`)
- `REPORTS_TABLE` (default `k9_reports`)
- `IMAGES_BUCKET` (default `k9-images`)
- `OPENSEARCH_ENDPOINT` (empty by default; set to enable search)
- `OPENSEARCH_INDEX` (default `products`)
- `AUTH_MODE` (`local` | `cognito`, default `local`)
- `JWT_SECRET` (default "change-me-in-prod" — you MUST override in non-dev)
- `JWT_ISSUER`, `JWT_AUDIENCE`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL`
- If using Cognito: `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`

## Running tests

Using `uv` (no activation required):

```bash
# Ensure Python 3.11 and sync runtime + dev dependencies
uv venv -p 3.11         # optional; uv will create .venv on first sync
uv sync --dev           # installs [project] + [dependency-groups.dev]

# Run tests through the managed environment
uv run pytest -q
```

With pip only:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
# Dev/test tools (approximate)
pip install pytest pytest-cov pytest-mock mypy ruff black isort boto3-stubs[essential]
pytest -q
```

Note: Runtime dependencies are packaged in Lambda Layers for AWS, but you still need local installs to run unit tests.

## Deploying to AWS

The easiest path is the provided deploy script (builds layers, runs `sam build`, then `sam deploy`).

1) Ensure AWS credentials are configured and you have the SAM CLI.
2) Optionally create or choose an OpenSearch endpoint (if you plan to use search).
3) Deploy:

```bash
# Basic deploy to us-east-1 with a dev stack name
./scripts/deploy.sh -e dev -r us-east-1 -s k9-api \
  --opensearch-endpoint "https://your-opensearch.example.com"   # optional
```

The script will:
- Build Lambda Layers from `requirements/`
- `sam build` the application
- `sam deploy` the CloudFormation stack `<stack>-<environment>` (e.g., `k9-api-dev`)

Outputs include:
- `HttpApiUrl` — your API base URL
- `ApiFunctionArn` — the Lambda function ARN

Retrieve the URL:

```bash
aws cloudformation describe-stacks \
  --stack-name k9-api-dev \
  --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" \
  --output text
```

### Important production settings

- JWT secret: Set a strong secret; don’t use the default.

```bash
# Example: set env vars after first deploy
aws lambda update-function-configuration \
  --function-name $(aws cloudformation describe-stack-resources \
    --stack-name k9-api-dev \
    --query "StackResources[?LogicalResourceId=='ApiFunction'].PhysicalResourceId" \
    --output text) \
  --environment "Variables={JWT_SECRET=$(openssl rand -hex 32),AUTH_MODE=local}"
```

- Cognito mode (optional): set `AUTH_MODE=cognito` and provide `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`.
- OpenSearch endpoint: pass at deploy time via `--parameter-overrides OpenSearchEndpoint=...` (the script’s `--opensearch-endpoint` flag) or update the function env later.
- Least-privilege: the template grants CRUD on DynamoDB tables and S3 bucket created by the stack. Review and tighten policies for your org.

### Clean up

Delete the stack to remove all resources:

```bash
aws cloudformation delete-stack --stack-name k9-api-dev
```

## Calling the API

After deploy, try a health check by hitting an unknown route (should be 404 JSON):

```bash
curl -i "$(aws cloudformation describe-stacks \
  --stack-name k9-api-dev \
  --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" \
  --output text)/does-not-exist"
```

See `api.md` for detailed request/response schemas. Auth endpoints issue JWTs; include `Authorization: Bearer <token>` for protected routes.

## Troubleshooting

- SAM local requires Docker. If `sam local start-api` hangs or errors, ensure Docker is running.
- Region mismatches: the app uses `AWS_REGION`/`AWS_DEFAULT_REGION`. Keep your AWS CLI/SAM region consistent with template deploys.
- OpenSearch disabled: if `OPENSEARCH_ENDPOINT` is empty, search routes may be limited or return graceful errors depending on configuration.
- Large dependencies: layers are split across `core`, `data`, `ml`. Ensure Python 3.11 is available for building.
- Permissions: make sure your IAM user/role can create CloudFormation stacks, Lambda, API Gateway, DynamoDB, S3 (and OpenSearch if used).

## License

Copyright © K9 Team. All rights reserved.
