#!/usr/bin/env bash
set -euo pipefail

# Creates: Cognito app client
# Usage: client.sh <dev|stage|prod> [--refresh]
# Reads from SSM:
# - /k9/<stage>/identity/cognito/user-pool-id
# Writes to SSM:
# - /k9/<stage>/identity/cognito/client-id
# - /k9/<stage>/identity/cognito/client-secret
# Rerun: yes, with --refresh

AWS_REGION="${AWS_REGION:-us-east-2}"
export AWS_PAGER=""

usage() {
  echo "Usage: $0 <dev|stage|prod> [--refresh]" >&2
  exit 1
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required"
}

aws_cli() {
  aws --region "$AWS_REGION" "$@"
}

validate_stage() {
  local stage="${1:-}"
  [[ "$stage" =~ ^(dev|stage|prod)$ ]] || usage
}

ssm_get() {
  aws_cli ssm get-parameter \
    --name "$1" \
    --query 'Parameter.Value' \
    --output text \
    2>/dev/null || return 1
}

ssm_put() {
  aws_cli ssm put-parameter \
    --name "$1" \
    --type String \
    --tier Standard \
    --value "$2" \
    --overwrite \
    >/dev/null
}

ssm_delete_if_exists() {
  aws_cli ssm delete-parameter --name "$1" >/dev/null 2>&1 || true
}

app_client_exists() {
  local user_pool_id="$1"
  local client_id="$2"

  aws_cli cognito-idp describe-user-pool-client \
    --user-pool-id "$user_pool_id" \
    --client-id "$client_id" \
    >/dev/null 2>&1
}

main() {
  need aws
  need jq

  local stage="${1:-}"
  local refresh_flag="${2:-}"
  local refresh=false

  validate_stage "$stage"
  [[ -z "$refresh_flag" || "$refresh_flag" == "--refresh" ]] || usage
  [[ "$refresh_flag" == "--refresh" ]] && refresh=true

  local client_name="k9-${stage}-admin-client"
  local ssm_pool_id="/k9/${stage}/identity/cognito/user-pool-id"
  local ssm_client_id="/k9/${stage}/identity/cognito/client-id"
  local ssm_client_secret="/k9/${stage}/identity/cognito/client-secret"

  local user_pool_id
  user_pool_id="$(ssm_get "$ssm_pool_id")" || die "Missing SSM parameter: $ssm_pool_id"

  if existing_client_id="$(ssm_get "$ssm_client_id")"; then
    $refresh || die "App client already exists. Rerun with --refresh."

    if app_client_exists "$user_pool_id" "$existing_client_id"; then
      echo "Deleting Cognito app client: $existing_client_id"
      aws_cli cognito-idp delete-user-pool-client \
        --user-pool-id "$user_pool_id" \
        --client-id "$existing_client_id" \
        >/dev/null
    fi

    ssm_delete_if_exists "$ssm_client_id"
    ssm_delete_if_exists "$ssm_client_secret"
  fi

  local payload
  payload="$(
    jq -cn \
      --arg pool_id "$user_pool_id" \
      --arg name "$client_name" '
      {
        UserPoolId: $pool_id,
        ClientName: $name,
        GenerateSecret: true,
        ExplicitAuthFlows: ["ALLOW_ADMIN_USER_PASSWORD_AUTH"],
        EnableTokenRevocation: true,
        RefreshTokenRotation: {
          Feature: "ENABLED",
          RetryGracePeriodSeconds: 0
        },
        RefreshTokenValidity: 1,
        AccessTokenValidity: 1,
        IdTokenValidity: 1,
        TokenValidityUnits: {
          RefreshToken: "days",
          AccessToken: "hours",
          IdToken: "hours"
        },
        ReadAttributes: [
          "custom:id",
          "preferred_username",
          "name",
          "picture",
          "custom:role",
          "custom:last_login_at",
          "updated_at"
        ],
        WriteAttributes: [
          "custom:id",
          "preferred_username",
          "name",
          "picture",
          "custom:role",
          "custom:last_login_at"
        ],
        SupportedIdentityProviders: ["COGNITO"]
      }
    '
  )"

  echo "Creating Cognito app client: $client_name"

  local create_output client_id client_secret
  create_output="$(
    aws_cli cognito-idp create-user-pool-client \
      --cli-input-json "$payload" \
      --query 'UserPoolClient' \
      --output json
  )"

  client_id="$(jq -r '.ClientId // empty' <<<"$create_output")"
  client_secret="$(jq -r '.ClientSecret // empty' <<<"$create_output")"

  [[ -n "$client_id" ]] || die "Failed to resolve client ID"
  [[ -n "$client_secret" ]] || die "Failed to resolve client secret"

  ssm_put "$ssm_client_id" "$client_id"
  ssm_put "$ssm_client_secret" "$client_secret"

  cat <<EOF
Created:
  Cognito app client: $client_name
Wrote to SSM:
  $ssm_client_id = $client_id
  $ssm_client_secret = [redacted]
EOF
}

main "$@"