#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="${ROOT_DIR}/template.yaml"
PORT=3001
BUILD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--port) PORT="$2"; shift 2;;
    --no-build) BUILD=0; shift;;
    -h|--help) echo "Usage: $0 [-p port] [--no-build]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

if [[ $BUILD -eq 1 ]]; then
  "${ROOT_DIR}/scripts/build.sh"
  sam build --template-file "${TEMPLATE}"
fi

sam local start-api \
  --template-file "${TEMPLATE}" \
  --port "${PORT}" \
  --host 0.0.0.0
