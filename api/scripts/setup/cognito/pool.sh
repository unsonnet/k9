#!/usr/bin/env bash
set -euo pipefail

# Creates: Cognito user pool
# Usage: pool.sh <dev|stage|prod>
# Reads from SSM: none
# Writes to SSM:
# - /k9/<stage>/identity/cognito/user-pool-id
# Rerun: no

AWS_REGION="${AWS_REGION:-us-east-2}"
export AWS_PAGER=""

usage() {
  echo "Usage: $0 <dev|stage|prod>" >&2
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

find_user_pool_id_by_name() {
  local pool_name="$1"
  local next_token=""
  local output
  local pool_id

  while true; do
    if [[ -n "$next_token" ]]; then
      output="$(aws_cli cognito-idp list-user-pools --max-results 60 --next-token "$next_token" --output json)"
    else
      output="$(aws_cli cognito-idp list-user-pools --max-results 60 --output json)"
    fi

    pool_id="$(
      jq -r --arg name "$pool_name" '
        .UserPools[]
        | select(.Name == $name)
        | .Id
      ' <<<"$output" | head -n1
    )"

    if [[ -n "$pool_id" ]]; then
      echo "$pool_id"
      return 0
    fi

    next_token="$(jq -r '.NextToken // empty' <<<"$output")"
    [[ -n "$next_token" ]] || break
  done

  return 1
}

main() {
  need aws
  need jq

  local stage="${1:-}"
  validate_stage "$stage"

  local pool_name="k9-${stage}-user-pool"
  local ssm_pool_id="/k9/${stage}/identity/cognito/user-pool-id"

  ssm_get "$ssm_pool_id" >/dev/null && die "SSM parameter already exists: $ssm_pool_id"

  if existing_pool_id="$(find_user_pool_id_by_name "$pool_name")"; then
    die "Cognito user pool already exists: $pool_name ($existing_pool_id)"
  fi

  local payload
  payload="$(
    jq -cn --arg name "$pool_name" '
      {
        PoolName: $name,
        AliasAttributes: ["preferred_username"],
        UsernameConfiguration: { CaseSensitive: true },
        Policies: {
          PasswordPolicy: {
            MinimumLength: 8,
            RequireUppercase: true,
            RequireLowercase: true,
            RequireNumbers: true,
            RequireSymbols: true,
            TemporaryPasswordValidityDays: 7
          },
          SignInPolicy: {
            AllowedFirstAuthFactors: ["PASSWORD"]
          }
        },
        MfaConfiguration: "OFF",
        Schema: [
          {
            Name: "id",
            AttributeDataType: "String",
            Mutable: false,
            Required: false,
            StringAttributeConstraints: { MinLength: "6", MaxLength: "64" }
          },
          {
            Name: "preferred_username",
            AttributeDataType: "String",
            Mutable: true,
            Required: true,
            StringAttributeConstraints: { MinLength: "1", MaxLength: "99" }
          },
          {
            Name: "name",
            AttributeDataType: "String",
            Mutable: true,
            Required: true,
            StringAttributeConstraints: { MinLength: "1", MaxLength: "2048" }
          },
          {
            Name: "picture",
            AttributeDataType: "String",
            Mutable: true,
            Required: false,
            StringAttributeConstraints: { MinLength: "1", MaxLength: "2048" }
          },
          {
            Name: "role",
            AttributeDataType: "String",
            Mutable: true,
            Required: false,
            StringAttributeConstraints: { MinLength: "1", MaxLength: "256" }
          },
          {
            Name: "last_login_at",
            AttributeDataType: "DateTime",
            Mutable: true,
            Required: false
          }
        ],
        AdminCreateUserConfig: {
          AllowAdminCreateUserOnly: true
        },
        AccountRecoverySetting: {
          RecoveryMechanisms: [
            { Name: "admin_only", Priority: 1 }
          ]
        },
        DeletionProtection: "ACTIVE"
      }
    '
  )"

  echo "Creating Cognito user pool: $pool_name"

  local user_pool_id
  user_pool_id="$(
    aws_cli cognito-idp create-user-pool \
      --cli-input-json "$payload" \
      --query 'UserPool.Id' \
      --output text
  )"

  [[ -n "$user_pool_id" && "$user_pool_id" != "None" ]] || die "Failed to resolve user pool ID"

  ssm_put "$ssm_pool_id" "$user_pool_id"

  cat <<EOF
Created:
  Cognito user pool: $pool_name
Wrote to SSM:
  $ssm_pool_id = $user_pool_id
EOF
}

main "$@"