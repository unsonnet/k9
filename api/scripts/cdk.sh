#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: scripts/cdk.sh <dev|stage|prod> <synth|diff|deploy>" >&2
  exit 1
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$repo_root/.env"

env_args=()
if [[ -f "$env_file" ]]; then
  env_args+=(--env-file "$env_file")
fi

uv run "${env_args[@]}" --project "$repo_root" "$repo_root/scripts/mkdocs.py"
cd "$repo_root/infra/cdk"

stage="${1:-dev}"
action="${2:-synth}"

case "$stage" in
  dev|stage|prod) ;;
  *) echo "invalid stage: $stage" >&2; usage ;;
esac

case "$action" in
  synth|diff|deploy) ;;
  *) echo "invalid action: $action" >&2; usage ;;
esac

capitalize() {
  local value="$1"
  local first="${value:0:1}"
  printf '%s%s' "${first^^}" "${value:1}"
}

stack_name="K9Api$(capitalize "$stage")Stack"

proxy_bypass_default="localhost,127.0.0.1,.amazonaws.com,.dkr.ecr.us-east-2.amazonaws.com,425688663965.dkr.ecr.us-east-2.amazonaws.com"
proxy_bypass_value="${NO_PROXY:-${no_proxy:-$proxy_bypass_default}}"

export NO_PROXY="$proxy_bypass_value"
export no_proxy="$proxy_bypass_value"

cmd=(
  uv run --project .
  cdk
  --context "stage=$stage"
  --asset-parallelism false
  --asset-prebuild false
)

if [[ "$action" == "deploy" ]]; then
  cmd+=(
    --require-approval never
    --outputs-file "../../cdk.out/outputs-${stage}.json"
  )
fi

exec "${cmd[@]}" "$action" "$stack_name"