#!/usr/bin/env bash
set -euo pipefail

# Runs CDK actions for a stage.
# Usage: cdk.sh <dev|stage|prod> <synth|diff|deploy>
# Rerun: yes

usage() {
  echo "Usage: $0 <dev|stage|prod> <synth|diff|deploy>" >&2
  exit 1
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required"
}

validate_stage() {
  local stage="${1:-}"
  [[ "$stage" =~ ^(dev|stage|prod)$ ]] || usage
}

validate_action() {
  local action="${1:-}"
  [[ "$action" =~ ^(synth|diff|deploy)$ ]] || usage
}

capitalize() {
  local value="$1"
  local first="${value:0:1}"
  printf '%s%s' "${first^^}" "${value:1}"
}

prepare_env() {
  local proxy_bypass_default="localhost,127.0.0.1,.amazonaws.com,.dkr.ecr.us-east-2.amazonaws.com,425688663965.dkr.ecr.us-east-2.amazonaws.com"
  local proxy_bypass_value="${NO_PROXY:-${no_proxy:-$proxy_bypass_default}}"

  export NO_PROXY="$proxy_bypass_value"
  export no_proxy="$proxy_bypass_value"

  export DOCKER_CLIENT_TIMEOUT=1200
  export COMPOSE_HTTP_TIMEOUT=1200
}

run_mkdocs() {
  local repo_root="$1"
  local env_file="$repo_root/.env"
  local -a env_args=()

  [[ -f "$env_file" ]] && env_args+=(--env-file "$env_file")

  uv run "${env_args[@]}" \
    --project "$repo_root" \
    "$repo_root/scripts/mkdocs.py"
}

run_cdk() {
  local repo_root="$1"
  local stage="$2"
  local action="$3"
  local stack_name="$4"

  cd "$repo_root/infra/cdk"

  local -a cmd=(
    uv run
    --project "$repo_root"
    cdk
    --context "stage=$stage"
    --asset-parallelism false
  )

  if [[ "$action" == "deploy" ]]; then
    cmd+=(
      --require-approval never
      --outputs-file "$repo_root/cdk.out/outputs-${stage}.json"
    )
  fi

  "${cmd[@]}" "$action" "$stack_name"
}

retry_deploy() {
  local repo_root="$1"
  local stage="$2"
  local stack_name="$3"
  local max_attempts=3
  local attempt
  local backoff
  local exit_code=1

  for attempt in 1 2 3; do
    echo
    echo "==========================================="
    echo "[CDK Deploy Attempt ${attempt}/${max_attempts}]"
    echo "==========================================="

    if run_cdk "$repo_root" "$stage" "deploy" "$stack_name"; then
      echo
      echo "Deployment succeeded."
      return 0
    fi

    exit_code=$?

    if (( attempt < max_attempts )); then
      backoff=$((60 * attempt))
      echo
      echo "Deployment failed. Retrying in ${backoff}s..."
      sleep "$backoff"
    fi
  done

  return "$exit_code"
}

main() {
  need uv

  local repo_root
  local stage="${1:-}"
  local action="${2:-}"

  validate_stage "$stage"
  validate_action "$action"

  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

  local stack_name="K9Api$(capitalize "$stage")Stack"

  prepare_env
  run_mkdocs "$repo_root"

  if [[ "$action" == "deploy" ]]; then
    retry_deploy "$repo_root" "$stage" "$stack_name"
  else
    exec bash -c 'cd "$1/infra/cdk" && shift && "$@"' _ \
      "$repo_root" \
      uv run --project "$repo_root" cdk --context "stage=$stage" --asset-parallelism false "$action" "$stack_name"
  fi
}

main "$@"