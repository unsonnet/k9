#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: scripts/sam.sh <synth|build|start-api|invoke-auth> [event.json]" >&2
  exit 1
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

action="${1:-start-api}"
cdk_template="infra/cdk/cdk.out/K9ApiDevStack.template.json"
built_template=".aws-sam/build/template.yaml"

synth() {
  scripts/cdk.sh dev synth >/dev/null
}

build() {
  synth
  sam build --template-file "$cdk_template"
}

case "$action" in
  synth)
    synth
    ;;
  build)
    build
    ;;
  start-api)
    build
    exec sam local start-api --template "$built_template"
    ;;
  invoke-auth)
    build
    exec sam local invoke AuthServiceFunction --template "$built_template" --event "${2:-events/auth.json}"
    ;;
  *)
    echo "invalid action: $action" >&2
    usage
    ;;
esac