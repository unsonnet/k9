#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# lib_build_layers.sh
# Build and optionally publish AWS Lambda Layers (core, data, ml)
# Safe for multi-user environments
# ------------------------------------------------------------------------------

set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib_common.sh"

require_tool uv
require_tool zip
require_tool aws

build_layers() {
  local stage="${1:-dev}"
  local publish="${2:-0}"
  local bucket="${LAYER_BUCKET_OVERRIDE:-k9-lambda-layers-${USER}-${stage}}"

  info "Building Lambda layers for stage '${stage}' (publish=${publish})"
  rm -rf "${LAYERS_DIR}"
  mkdir -p "${LAYERS_DIR}" "${REQ_DIR}"

  info "Exporting per-layer requirements (no dev dependencies)"
  uv export --locked --format requirements-txt --only-group core -o "${REQ_DIR}/core.txt"
  uv export --locked --format requirements-txt --only-group data -o "${REQ_DIR}/data.txt"
  uv export --locked --format requirements-txt --only-group ml   -o "${REQ_DIR}/ml.txt"

  build_one() {
    local name="$1"
    local req="${REQ_DIR}/${name}.txt"
    local out="${LAYERS_DIR}/${name}/python"

    info "Installing layer '${name}'"
    mkdir -p "${out}"

    UV_LINK_MODE=copy uv pip install \
      --no-cache-dir \
      --python "${PYTHON_VERSION}" \
      --python-platform "${PYTHON_PLATFORM}" \
      -r "${req}" \
      --target "${out}" \
      --upgrade --quiet

    find "${out}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${out}" -type f -name "*.pyc" -delete 2>/dev/null || true
  }

  build_one core
  build_one data
  build_one ml

  if [[ "${publish}" -eq 1 ]]; then
    ensure_aws_profile
    info "Publishing layers to AWS (S3 bucket: ${bucket})"
    aws s3 mb "s3://${bucket}" --region "${REGION}" >/dev/null 2>&1 || true

    publish_layer() {
      local name="$1"
      local dir="${LAYERS_DIR}/${name}"
      local zip="${LAYERS_DIR}/${name}.zip"
      local key="${name}-${stage}.zip"

      info "Packaging '${name}' layer"
      (cd "${dir}" && zip -r9q "../${name}.zip" python)

      info "Uploading ${zip} to s3://${bucket}/${key}"
      aws s3 cp "${zip}" "s3://${bucket}/${key}" \
        --region "${REGION}" \
        --profile "${AWS_PROFILE:-default}" >/dev/null

      info "Publishing Lambda layer '${name}'"
      aws lambda publish-layer-version \
        --layer-name "k9-${name}-${stage}" \
        --description "K9 ${name} layer (${stage})" \
        --content "S3Bucket=${bucket},S3Key=${key}" \
        --region "${REGION}" \
        --compatible-runtimes "python3.11" \
        --query "LayerVersionArn" \
        --output text \
        --profile "${AWS_PROFILE:-default}"
    }

    local core_arn data_arn ml_arn
    core_arn="$(publish_layer core | tr -d '\r' | tail -n 1)"
    data_arn="$(publish_layer data | tr -d '\r' | tail -n 1)"
    ml_arn="$(publish_layer ml | tr -d '\r' | tail -n 1)"

    {
      echo "CORE_LAYER_ARN=${core_arn}"
      echo "DATA_LAYER_ARN=${data_arn}"
      echo "ML_LAYER_ARN=${ml_arn}"
    } > "${LAYERS_DIR}/${stage}_arns.env"

    ok "Saved ARNs → ${LAYERS_DIR}/${stage}_arns.env"
  fi

  ok "Layer build complete"
}
