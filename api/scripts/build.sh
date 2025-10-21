#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAYERS_DIR="${ROOT_DIR}/layers"
REQ_DIR="${ROOT_DIR}/requirements"

PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
# Use the right platform triple for your Lambda architecture:
#  x86_64: x86_64-unknown-linux-gnu
#  arm64 (Graviton): aarch64-unknown-linux-gnu
PYTHON_PLATFORM="${PYTHON_PLATFORM:-x86_64-unknown-linux-gnu}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[error] 'uv' is required. Install from https://docs.astral.sh/uv/ and retry." >&2
  exit 1
fi

echo "[build] Cleaning previous artifacts"
rm -rf "${LAYERS_DIR}"
mkdir -p "${LAYERS_DIR}" "${REQ_DIR}"

echo "[build] Exporting per-layer requirements from lockfile"
# NOTE: uv 0.8.0 supports selecting dependency groups during export.
# We export to requirements.txt format for pip-style installation.  :contentReference[oaicite:2]{index=2}
uv export --locked --format requirements-txt --group core -o "${REQ_DIR}/core.txt"
uv export --locked --format requirements-txt --group data -o "${REQ_DIR}/data.txt"
uv export --locked --format requirements-txt --group ml   -o "${REQ_DIR}/ml.txt"

build_layer() {
  local name="$1"; shift
  local req="${REQ_DIR}/${name}.txt"
  local out="${LAYERS_DIR}/${name}/python"

  echo "[build] Layer ${name}"
  mkdir -p "${out}"

  # Install pre-resolved requirements into the layer dir.
  # --python sets markers, --python-platform picks Linux wheels for Lambda.  :contentReference[oaicite:3]{index=3}
  UV_LINK_MODE=copy \
  uv pip install \
    --python "${PYTHON_VERSION}" \
    --python-platform "${PYTHON_PLATFORM}" \
    -r "${req}" \
    --target "${out}" \
    --upgrade --quiet
}

build_layer core
build_layer data
build_layer ml

echo "[build] Done"
