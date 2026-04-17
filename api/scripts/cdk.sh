#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: scripts/cdk.sh <dev|stage|prod> <synth|diff|deploy>" >&2
  exit 1
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

cmd=(
  uv run --project .
  cdk
  --context "stage=$stage"
)

if [[ "$action" == "deploy" ]]; then
  cmd+=(
    --require-approval never
    --outputs-file "../../cdk.out/outputs-${stage}.json"
  )
fi

exec "${cmd[@]}" "$action" "$stack_name"