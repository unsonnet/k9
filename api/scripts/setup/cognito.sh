#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - Cognito User Pool: k9-<stage>-user-pool
#   - Cognito User Pool App Client: k9-<stage>-admin-client
# Stores to SSM:
#   - /k9/<stage>/identity/cognito/client-id
#   - /k9/<stage>/identity/cognito/client-secret
#   - /k9/<stage>/identity/cognito/user-pool-id

AWS_REGION="${AWS_REGION:-us-east-2}"
export AWS_PAGER=""

usage() { echo "Usage: $0 <dev|stage|prod>" >&2; exit 1; }
die()   { echo "ERROR: $*" >&2; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }
aws_cli() { aws --region "$AWS_REGION" "$@"; }

put_ssm_string() {
  aws_cli ssm put-parameter \
    --name "$1" \
    --type String \
    --tier Standard \
    --value "$2" \
    --overwrite \
    >/dev/null
}

ssm_exists() { aws_cli ssm get-parameter --name "$1" >/dev/null 2>&1; }

cleanup() {
  rm -f "${POOL_JSON:-}" "${CLIENT_JSON:-}"
}
trap cleanup EXIT

require aws
require jq

STAGE="${1:-}"
[[ "$STAGE" =~ ^(dev|stage|prod)$ ]] || usage

POOL_NAME="k9-${STAGE}-user-pool"
CLIENT_NAME="k9-${STAGE}-admin-client"

SSM_CLIENT_ID="/k9/${STAGE}/identity/cognito/client-id"
SSM_CLIENT_SECRET="/k9/${STAGE}/identity/cognito/client-secret"
SSM_USER_POOL_ID="/k9/${STAGE}/identity/cognito/user-pool-id"

preflight() {
  local -a issues=()
  local existing_pool_id=""

  for name in "$SSM_USER_POOL_ID" "$SSM_CLIENT_ID" "$SSM_CLIENT_SECRET"; do
    ssm_exists "$name" && issues+=("SSM parameter already exists: $name")
  done

  existing_pool_id="$(
    aws_cli cognito-idp list-user-pools --max-results 60 --output json \
      | jq -r --arg pool_name "$POOL_NAME" '
          .UserPools[]
          | select(.Name == $pool_name)
          | .Id
        ' \
      | head -n1
  )"

  [[ -n "$existing_pool_id" ]] && \
    issues+=("Cognito user pool already exists: $POOL_NAME ($existing_pool_id)")

  if ((${#issues[@]} > 0)); then
    echo "Preflight failed. Fix these issues, then rerun:" >&2
    printf '  - %s\n' "${issues[@]}" >&2
    exit 1
  fi
}

create_pool_payload() {
  jq -n --arg pool_name "$POOL_NAME" '
    {
      PoolName: $pool_name,
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
          Required: true,
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
      AdminCreateUserConfig: { AllowAdminCreateUserOnly: true },
      AccountRecoverySetting: {
        RecoveryMechanisms: [{ Name: "admin_only", Priority: 1 }]
      },
      DeletionProtection: "INACTIVE"
    }
  '
}

create_client_payload() {
  jq -n --arg user_pool_id "$USER_POOL_ID" --arg client_name "$CLIENT_NAME" '
    {
      UserPoolId: $user_pool_id,
      ClientName: $client_name,
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
        "preferred_username",
        "name",
        "picture",
        "custom:role",
        "custom:last_login_at",
        "updated_at"
      ],
      WriteAttributes: [
        "preferred_username",
        "name",
        "picture",
        "custom:role",
        "custom:last_login_at"
      ],
      SupportedIdentityProviders: ["COGNITO"]
    }
  '
}

preflight

echo "Creating Cognito user pool: $POOL_NAME"

POOL_JSON="$(mktemp)"
create_pool_payload >"$POOL_JSON"

CREATE_POOL_OUTPUT="$(
  aws_cli cognito-idp create-user-pool --cli-input-json "file://$POOL_JSON"
)"

USER_POOL_ID="$(jq -r '.UserPool.Id // empty' <<<"$CREATE_POOL_OUTPUT")"
[[ -n "$USER_POOL_ID" ]] || die "Failed to create user pool or parse UserPool.Id."

echo "Enabling software token MFA"

aws_cli cognito-idp set-user-pool-mfa-config \
  --user-pool-id "$USER_POOL_ID" \
  --software-token-mfa-configuration Enabled=true \
  --mfa-configuration OPTIONAL \
  >/dev/null

echo "Creating Cognito app client: $CLIENT_NAME"

CLIENT_JSON="$(mktemp)"
create_client_payload >"$CLIENT_JSON"

CREATE_CLIENT_OUTPUT="$(
  aws_cli cognito-idp create-user-pool-client --cli-input-json "file://$CLIENT_JSON"
)"

CLIENT_ID="$(jq -r '.UserPoolClient.ClientId // empty' <<<"$CREATE_CLIENT_OUTPUT")"
CLIENT_SECRET="$(jq -r '.UserPoolClient.ClientSecret // empty' <<<"$CREATE_CLIENT_OUTPUT")"

[[ -n "$CLIENT_ID" ]]     || die "Failed to create app client or parse ClientId."
[[ -n "$CLIENT_SECRET" ]] || die "Failed to create app client or parse ClientSecret."

put_ssm_string "$SSM_USER_POOL_ID" "$USER_POOL_ID"
put_ssm_string "$SSM_CLIENT_ID" "$CLIENT_ID"
put_ssm_string "$SSM_CLIENT_SECRET" "$CLIENT_SECRET"

cat <<EOF

Created Cognito resources:
  Stage:         $STAGE
  Region:        $AWS_REGION
  UserPoolName:  $POOL_NAME
  UserPoolId:    $USER_POOL_ID
  ClientName:    $CLIENT_NAME
  ClientId:      $CLIENT_ID

Stored in SSM:
  $SSM_USER_POOL_ID
  $SSM_CLIENT_ID
  $SSM_CLIENT_SECRET
EOF