#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAYERS_DIR="${ROOT_DIR}/layers"
PY_VER="python3.11"

echo "[build] Cleaning previous artifacts"
rm -rf "${LAYERS_DIR}"
mkdir -p "${LAYERS_DIR}"

build_layer() {
  local name="$1"; shift
  local req="${ROOT_DIR}/requirements/${name}.txt"
  local out="${LAYERS_DIR}/${name}/python"
  echo "[build] Layer ${name} from ${req}"
  mkdir -p "${out}"
  if [[ ! -f "${req}" ]]; then
    echo "[warn] requirements file not found: ${req} (skipping)"
    return 0
  fi
  if command -v uv >/dev/null 2>&1; then
    uv pip install --python "${PY_VER}" -r "${req}" -t "${out}" --quiet
  else
    "${PY_VER}" -m pip install -r "${req}" -t "${out}" --upgrade --quiet
  fi
}

build_layer core
build_layer data
build_layer ml

echo "[build] Done"
