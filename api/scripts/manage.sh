#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# manage.sh
# Unified CLI entrypoint for K9 API (build / deploy / dev / diagnose)
# Safe for multi-user AWS environments
# ------------------------------------------------------------------------------

set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib_common.sh"
source "$(dirname "${BASH_SOURCE[0]}")/lib_build_layers.sh"

# ------------------------------------------------------------------------------
# Environment defaults (non-destructive)
# ------------------------------------------------------------------------------
export AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"
export AWS_DEFAULT_REGION="$AWS_REGION"

BUILD_TEMPLATE="${ROOT_DIR}/.aws-sam/build/template.yaml"

usage() {
  cat <<EOF
Usage: $0 <command> [options]

Commands:
  build       Build Lambda layers (optionally publish)
  deploy      Deploy full stack to AWS
  dev         Run local API (SAM Local)
  clean       Remove build artifacts
  diagnose    Inspect environment and configuration

Run '$0 <command> --help' for command-specific options.
EOF
}

# ------------------------------------------------------------------------------
# Safety guards
# ------------------------------------------------------------------------------
if [[ $EUID -eq 0 ]]; then
  warn "Running as root is discouraged. Waiting 3s..."
  sleep 3
fi

cmd="${1:-}"
shift || true

case "$cmd" in
  build)
    stage="dev"; publish=0
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --stage) stage="$2"; shift 2;;
        --publish) publish=1; shift;;
        -h|--help)
          echo "Usage: $0 build [--stage <env>] [--publish]"
          exit 0;;
        *) error "Unknown arg: $1";;
      esac
    done
    build_layers "$stage" "$publish"
    ;;

  deploy)
    ENV="dev"; STACK="k9-api"; USE_PUBLISHED=0; OPENSEARCH=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --stage|-e) ENV="$2"; shift 2;;
        --stack|-s) STACK="$2"; shift 2;;
        --use-published) USE_PUBLISHED=1; shift;;
        --opensearch-endpoint) OPENSEARCH="$2"; shift 2;;
        -h|--help)
          echo "Usage: $0 deploy [--stage dev|prod] [--use-published] [--opensearch-endpoint URL]"
          exit 0;;
        *) error "Unknown arg: $1";;
      esac
    done

    ensure_aws_profile

    if [[ "$ENV" == "prod" ]]; then
      read -p "⚠️  Confirm deployment to PROD (y/N): " confirm
      [[ "$confirm" =~ ^[Yy]$ ]] || error "Aborted by user."
    fi

    if [[ "$USE_PUBLISHED" -eq 1 ]]; then
      build_layers "$ENV" 1
      source "${LAYERS_DIR}/${ENV}_arns.env"
      PARAMS=( "UseArnLayers=true" "CoreLayerArn=$CORE_LAYER_ARN" "DataLayerArn=$DATA_LAYER_ARN" "MLLayerArn=$ML_LAYER_ARN" )
    else
      build_layers "$ENV" 0
      PARAMS=( "UseArnLayers=false" )
    fi

    info "Building SAM package"
    sam build --use-container  --template-file "$TEMPLATE" --parameter-overrides "${PARAMS[@]}"

    info "Deploying stack ${STACK}-${ENV}"
    sam deploy \
      --stack-name "${STACK}-${ENV}" \
      --region "${REGION}" \
      --capabilities CAPABILITY_IAM \
      --parameter-overrides OpenSearchEndpoint="${OPENSEARCH}" "${PARAMS[@]}" \
      --resolve-s3 --no-fail-on-empty-changeset

    ok "Deployment complete"
    ;;

  dev)
    PORT=3001; RELOAD=0; LIVE=0; FORCE_ARN=-1; ENV="dev"; BIND_HOST="127.0.0.1"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --reload) RELOAD=1; shift;;
        --live) LIVE=1; shift;;
        --use-arn) FORCE_ARN=1; shift;;
        --no-arn) FORCE_ARN=0; shift;;
        --bind) BIND_HOST="$2"; shift 2;;
        --stage|-e) ENV="$2"; shift 2;;
        -p|--port) PORT="$2"; shift 2;;
        -h|--help)
          echo "Usage: $0 dev [--live] [--reload] [--use-arn|--no-arn] [--bind host] [-p port]"
          exit 0;;
        *) error "Unknown arg: $1";;
      esac
    done

    USE_PUBLISHED=0
    PARAMS=( "UseArnLayers=false" )
    if [[ $FORCE_ARN -eq 1 ]]; then
      USE_PUBLISHED=1
    elif [[ $FORCE_ARN -eq 0 ]]; then
      USE_PUBLISHED=0
    elif [[ -f "${LAYERS_DIR}/${ENV}_arns.env" ]]; then
      source "${LAYERS_DIR}/${ENV}_arns.env"
      if [[ -n "${CORE_LAYER_ARN:-}" && -n "${DATA_LAYER_ARN:-}" && -n "${ML_LAYER_ARN:-}" ]]; then
        USE_PUBLISHED=1
      fi
    fi

    if [[ $USE_PUBLISHED -eq 1 ]]; then
      info "Using published ARN layers for local dev"
      PARAMS=(
        "UseArnLayers=true"
        "CoreLayerArn=${CORE_LAYER_ARN}"
        "DataLayerArn=${DATA_LAYER_ARN}"
        "MLLayerArn=${ML_LAYER_ARN}"
      )
    else
      info "Using local layers for dev build"
      build_layers "$ENV" 0
    fi

    if [[ $RELOAD -eq 1 ]]; then
      info "Reload requested, rebuilding function package"
      sam build --use-container  --template-file "$TEMPLATE" --parameter-overrides "${PARAMS[@]}"
    elif [[ ! -f "$BUILD_TEMPLATE" ]]; then
      info "First build — creating local package"
      sam build --use-container --template-file "$TEMPLATE" --parameter-overrides "${PARAMS[@]}"
    fi

    info "Starting local API on port $PORT [layers: $([[ $USE_PUBLISHED -eq 1 ]] && echo ARNs || echo local)]"
    sam local start-api \
      --template-file "$TEMPLATE" \
      --parameter-overrides "${PARAMS[@]}" \
      --warm-containers LAZY \
      --skip-pull-image \
      --port "$PORT" \
      --host "$BIND_HOST" \
      --env-vars <(cat <<EOF
{
  "ApiFunction": {
    "AWS_REGION": "${REGION}",
    "AWS_DEFAULT_REGION": "${REGION}"
  }
}
EOF
)
    ;;

  clean)
    info "Cleaning SAM build artifacts"
    rm -rf .aws-sam/build || true
    ok "Clean complete"
    ;;

  diagnose)
    echo -e "${bold}--- Environment Diagnostic Report ---${reset}"
    echo
    echo -e "${blue}Repository:${reset}  $ROOT_DIR"
    echo -e "${blue}Layers Dir:${reset}   $LAYERS_DIR"
    echo -e "${blue}Template:${reset}     $TEMPLATE"
    echo -e "${blue}Python:${reset}       ${PYTHON_VERSION} (${PYTHON_PLATFORM})"
    echo
    echo -e "${bold}AWS Configuration${reset}"
    echo -e "  Profile: ${AWS_PROFILE:-default}"
    echo -e "  Region:  ${AWS_REGION}"
    echo -e "  Bucket:  ${LAYER_BUCKET_OVERRIDE:-k9-lambda-layers-${USER}-<stage>}"
    echo
    echo -e "${bold}Toolchain${reset}"
    for tool in uv aws sam zip; do
      if command -v "$tool" >/dev/null 2>&1; then
        echo -e "  ${green}✓${reset} $tool → $(command -v "$tool")"
      else
        echo -e "  ${red}✗${reset} $tool (missing)"
      fi
    done
    echo
    echo -e "${bold}AWS Identity Check${reset}"
    if aws sts get-caller-identity >/dev/null 2>&1; then
      id=$(aws sts get-caller-identity --query "Arn" --output text)
      echo -e "  ${green}✓${reset} Authenticated as: ${id}"
    else
      echo -e "  ${red}✗${reset} AWS not logged in or credentials invalid"
    fi
    echo
    echo -e "${bold}System${reset}"
    echo -e "  User: $(whoami)"
    echo -e "  Shell: $SHELL"
    echo -e "  OS: $(uname -srmo)"
    echo
    ok "Diagnostics complete"
    ;;

  *)
    usage
    ;;
esac
