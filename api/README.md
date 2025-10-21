# K9 API — Serverless Backend

K9 API is a Python serverless backend exposing REST endpoints for authentication, users, products, reports, and search.  
It runs on AWS Lambda (Python 3.11) using AWS SAM, with DynamoDB and S3 as data stores and optional OpenSearch for search integration.

Docs: see `api.md` (Markdown reference) or `docs/api.html` (HTML reference).

---

## 🔍 Overview

**Runtime:** Python 3.11 (AWS Lambda)  
**Architecture:** API Gateway → Lambda → DynamoDB/S3/OpenSearch  
**Deployment:** AWS SAM + CloudFormation  
**Dependencies:** Managed via `uv`, layered into `core`, `data`, and `ml` Lambda Layers  

### Data & Services
- **DynamoDB** — `ProductsTable`, `UsersTable`, `ReportsTable` (GSI: `author-index`)
- **S3** — stores normalized product images
- **OpenSearch** — optional; configurable endpoint
- **Auth** — local JWT (HS256) or Cognito (RS256)

### Key Files
| File | Purpose |
|------|----------|
| `template.yaml` | SAM template defining AWS resources and environment variables |
| `src/app.py` | Entry point (Lambda handler + router) |
| `scripts/manage.sh` | Unified CLI for build, deploy, and local development |
| `scripts/lib_common.sh` | Shared utilities for environment setup and colorized output |
| `scripts/lib_build_layers.sh` | Logic for building and publishing Lambda Layers |
| `requirements/*.txt` | Layer dependency exports |

---

## 📁 Repository Layout

```
src/
  app.py
  handlers/       # per-domain route handlers
  services/       # data access and business logic
  models/         # Pydantic data models and schemas
  utils/          # shared helper utilities
scripts/
  manage.sh           # main CLI for build, deploy, dev
  lib_common.sh       # common env utilities
  lib_build_layers.sh # layer build/publish logic
docs/
  api.md, api.html
requirements/
  core.txt, data.txt, ml.txt
tests/
```

---

## ⚙️ Prerequisites

- **Python 3.11** (exact runtime required for Lambda)  
- **Docker** (required for `sam local`)  
- **AWS CLI v2** and **AWS SAM CLI**  
- **`uv`** ≥ 0.8.0 (for dependency locking and export)  
- IAM permissions for CloudFormation, Lambda, API Gateway, DynamoDB, S3, and OpenSearch (if used)

---

## 🧩 Local Development

Run the API locally using the unified management script.  
The tool automatically detects whether published `dev` layer ARNs exist (`layers/dev_arns.env`) and uses them; otherwise, it builds local layers.

### Command

```bash
./scripts/manage.sh dev
```

### Options
| Flag | Description |
|------|--------------|
| `--reload` | Rebuild layers and SAM before starting |
| `--live` | Mount `src/` directly to reflect live code changes |
| `--use-arn` | Force using published Lambda Layer ARNs |
| `--no-arn` | Force using local layer directories |
| `-p PORT` | Specify local port (default 3001) |

### Examples

```bash
# start using local layers (auto-detects ARNs if available)
./scripts/manage.sh dev

# live mode with hot-reloaded code
./scripts/manage.sh dev --live

# force rebuild before running
./scripts/manage.sh dev --reload

# force using published dev ARNs
./scripts/manage.sh dev --use-arn

# force using local layers
./scripts/manage.sh dev --no-arn
```

When running, access the API at [http://localhost:3001](http://localhost:3001).

---

## 🧱 Build Layers

Builds dependency layers from `pyproject.toml` and `uv.lock`.  
Layers are grouped as `core`, `data`, and `ml` and are reused by all functions.

### Command

```bash
./scripts/manage.sh build
```

### Options
| Flag | Description |
|------|--------------|
| `--stage NAME` | Stage name (`dev`, `staging`, `prod`) |
| `--publish` | Build and publish layers to AWS Lambda for the selected stage |

### Examples

```bash
# build local layers only
./scripts/manage.sh build

# build and publish dev layers (saves ARNs to layers/dev_arns.env)
./scripts/manage.sh build --stage dev --publish
```

Layer ARNs are automatically stored in `layers/<stage>_arns.env` for reuse in deploy and dev modes.

---

## 🚀 Deployment

Deploys the API stack to AWS using SAM.  
Supports both local and published layers.

### Command

```bash
./scripts/manage.sh deploy --stage dev
```

### Options
| Flag | Description |
|------|--------------|
| `--stage` | Environment (`dev`, `staging`, `prod`) |
| `--region` | AWS region (default from `AWS_DEFAULT_REGION` or `us-east-1`) |
| `--stack` | Stack name prefix (default `k9-api`) |
| `--opensearch-endpoint` | Optional OpenSearch URL |
| `--use-published` | Build and publish layers before deploy, using their ARNs |

### Examples

```bash
# deploy dev stack with local layers
./scripts/manage.sh deploy --stage dev

# deploy production stack with published layers
./scripts/manage.sh deploy --stage prod --use-published
```

Outputs include:
- **`HttpApiUrl`** — base URL of the API  
- **`ApiFunctionArn`** — ARN of the deployed Lambda function  

Retrieve API URL:

```bash
aws cloudformation describe-stacks   --stack-name k9-api-dev   --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue"   --output text
```

---

## 🔑 Environment Variables

These are defined in `template.yaml` and injected into the Lambda runtime.  
You can override them post-deployment using `aws lambda update-function-configuration`.

| Variable | Description |
|-----------|--------------|
| `AWS_REGION` | Lambda region (e.g., `us-east-1`) |
| `PRODUCTS_TABLE`, `USERS_TABLE`, `REPORTS_TABLE` | DynamoDB tables |
| `IMAGES_BUCKET` | S3 bucket for images |
| `OPENSEARCH_ENDPOINT` | Optional OpenSearch endpoint |
| `OPENSEARCH_INDEX` | Default: `products` |
| `AUTH_MODE` | `local` or `cognito` |
| `JWT_SECRET` | **must be overridden in production** |
| `JWT_ISSUER`, `JWT_AUDIENCE` | JWT claims |
| `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL` | Token lifetimes (seconds) |

---

## 🧪 Testing

Run unit tests using `pytest`. Both `uv` and pip environments are supported.

### Using uv

```bash
uv sync --dev
uv run pytest -q
```

### Using pip

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov mypy ruff black isort
pytest -q
```

---

## 🧹 Clean Up

Remove deployed resources by deleting the CloudFormation stack:

```bash
aws cloudformation delete-stack --stack-name k9-api-dev
```

---

## 🩺 Troubleshooting

| Issue | Cause / Resolution |
|--------|--------------------|
| Docker not running | Required for SAM local runtime |
| Region mismatch | Ensure `AWS_REGION` and CLI region match |
| OpenSearch missing | Routes degrade gracefully if endpoint is unset |
| Large dependencies | Layers (`core`, `data`, `ml`) isolate heavy libs |
| Missing permissions | Ensure IAM rights for CloudFormation, Lambda, API Gateway, DynamoDB, S3, OpenSearch |

---

## 📜 License

© K9 Team. All rights reserved.
