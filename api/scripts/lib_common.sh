#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# lib_common.sh
# Shared functions and environment setup for K9 scripts
# ------------------------------------------------------------------------------

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAYERS_DIR="${ROOT_DIR}/layers"
REQ_DIR="${ROOT_DIR}/requirements"
TEMPLATE="${ROOT_DIR}/template.yaml"
REGION="${AWS_DEFAULT_REGION:-us-east-2}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
PYTHON_PLATFORM="${PYTHON_PLATFORM:-x86_64-unknown-linux-gnu}"

# --- Pretty output ------------------------------------------------------------
bold="\033[1m"; reset="\033[0m"
blue="\033[1;34m"; green="\033[1;32m"; yellow="\033[1;33m"; red="\033[1;31m"

info()  { echo -e "${blue}[info]${reset} $*"; }
ok()    { echo -e "${green}[ok]${reset} $*"; }
warn()  { echo -e "${yellow}[warn]${reset} $*" >&2; }
error() { echo -e "${red}[error]${reset} $*" >&2; exit 1; }

# --- Tool checks --------------------------------------------------------------
require_tool() {
  local tool="$1"
  if ! command -v "$tool" >/dev/null 2>&1; then
    error "Required tool '${tool}' not found. Please install it first."
  fi
}

# --- AWS helper ---------------------------------------------------------------
ensure_aws_profile() {
  if [[ -z "${AWS_PROFILE:-}" ]]; then
    warn "No AWS_PROFILE set; using default profile."
  else
    info "Using AWS profile: ${AWS_PROFILE}"
  fi

  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    error "AWS credentials not available. Run 'aws sso login --profile ${AWS_PROFILE:-default}' first."
  fi
}
