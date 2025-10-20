#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="${ROOT_DIR}/template.yaml"

ENVIRONMENT="dev"
REGION="us-east-1"
STACK="k9-api"
OPENSEARCH_ENDPOINT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--environment) ENVIRONMENT="$2"; shift 2;;
    -r|--region) REGION="$2"; shift 2;;
    -s|--stack) STACK="$2"; shift 2;;
    --opensearch-endpoint) OPENSEARCH_ENDPOINT="$2"; shift 2;;
    -h|--help)
      echo "Usage: $0 [-e env] [-r region] [-s stack] [--opensearch-endpoint host]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

echo "[deploy] Building layers"
"${ROOT_DIR}/scripts/build.sh"

echo "[deploy] SAM build"
sam build --template-file "${TEMPLATE}"

echo "[deploy] SAM deploy"
sam deploy \
  --stack-name "${STACK}-${ENVIRONMENT}" \
  --region "${REGION}" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides OpenSearchEndpoint="${OPENSEARCH_ENDPOINT}" \
  --resolve-s3 \
  --no-fail-on-empty-changeset

echo "[deploy] Done"
