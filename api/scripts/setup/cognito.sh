#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - Cognito User Pool: k9-user-pool
#   - Cognito User Pool App Client: k9-admin-client

POOL_NAME="k9-user-pool"
CLIENT_NAME="k9-admin-client"
AWS_REGION="us-east-2"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: $1 is required." >&2
    exit 1
  }
}

json_get() {
  jq -r "$1"
}

cleanup() {
  rm -f "${POOL_JSON:-}" "${CLIENT_JSON:-}"
}

trap cleanup EXIT

require aws
require jq

create_pool_payload() {
  jq -n --arg pool_name "$POOL_NAME" '
    {
      PoolName: $pool_name,
      AliasAttributes: ["preferred_username"],
      UsernameConfiguration: {
        CaseSensitive: true
      },
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
          StringAttributeConstraints: {
            MinLength: "1",
            MaxLength: "99"
          }
        },
        {
          Name: "name",
          AttributeDataType: "String",
          Mutable: true,
          Required: true,
          StringAttributeConstraints: {
            MinLength: "1",
            MaxLength: "2048"
          }
        },
        {
          Name: "picture",
          AttributeDataType: "String",
          Mutable: true,
          Required: true,
          StringAttributeConstraints: {
            MinLength: "1",
            MaxLength: "2048"
          }
        },
        {
          Name: "role",
          AttributeDataType: "String",
          Mutable: true,
          Required: false,
          StringAttributeConstraints: {
            MinLength: "1",
            MaxLength: "256"
          }
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
          {
            Name: "admin_only",
            Priority: 1
          }
        ]
      },
      DeletionProtection: "INACTIVE"
    }
  '
}

create_client_payload() {
  jq -n \
    --arg user_pool_id "$USER_POOL_ID" \
    --arg client_name "$CLIENT_NAME" '
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

echo "Creating Cognito user pool: $POOL_NAME"

POOL_JSON="$(mktemp)"
create_pool_payload > "$POOL_JSON"

CREATE_POOL_OUTPUT="$(
  aws cognito-idp create-user-pool \
    --region "$AWS_REGION" \
    --cli-input-json "file://$POOL_JSON"
)"

USER_POOL_ID="$(printf '%s' "$CREATE_POOL_OUTPUT" | json_get '.UserPool.Id')"

if [[ -z "$USER_POOL_ID" || "$USER_POOL_ID" == "null" ]]; then
  echo "ERROR: Failed to create user pool or parse UserPool.Id." >&2
  echo "$CREATE_POOL_OUTPUT" >&2
  exit 1
fi

echo "Enabling software token MFA"

aws cognito-idp set-user-pool-mfa-config \
  --region "$AWS_REGION" \
  --user-pool-id "$USER_POOL_ID" \
  --software-token-mfa-configuration Enabled=true \
  --mfa-configuration OPTIONAL >/dev/null

echo "Creating Cognito app client: $CLIENT_NAME"

CLIENT_JSON="$(mktemp)"
create_client_payload > "$CLIENT_JSON"

CREATE_CLIENT_OUTPUT="$(
  aws cognito-idp create-user-pool-client \
    --region "$AWS_REGION" \
    --cli-input-json "file://$CLIENT_JSON"
)"

CLIENT_ID="$(printf '%s' "$CREATE_CLIENT_OUTPUT" | json_get '.UserPoolClient.ClientId')"
CLIENT_SECRET="$(printf '%s' "$CREATE_CLIENT_OUTPUT" | json_get '.UserPoolClient.ClientSecret')"

if [[ -z "$CLIENT_ID" || "$CLIENT_ID" == "null" ]]; then
  echo "ERROR: Failed to create app client or parse ClientId." >&2
  echo "$CREATE_CLIENT_OUTPUT" >&2
  exit 1
fi

cat <<EOF

Created Cognito resources:
  Region:        $AWS_REGION
  UserPoolName:  $POOL_NAME
  UserPoolId:    $USER_POOL_ID
  ClientName:    $CLIENT_NAME
  ClientId:      $CLIENT_ID
  ClientSecret:  $CLIENT_SECRET

Effective MFA configuration:
  MfaConfiguration: OPTIONAL
  EnabledMfas:      SOFTWARE_TOKEN_MFA

Readable by app client:
  - preferred_username
  - name
  - picture
  - custom:role
  - custom:last_login_at
  - updated_at

Writable by app client:
  - preferred_username
  - name
  - picture
  - custom:role
  - custom:last_login_at

Password policy note:
  Cognito enforces:
    - minimum length: 8
    - uppercase required
    - lowercase required
    - number required
    - symbol required
EOF