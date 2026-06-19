#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - DynamoDB table: k9-<stage>-companies
# Stores to SSM:
#   - /k9/<stage>/data/dynamodb/table
#   - /k9/<stage>/data/dynamodb/stream/companies

AWS_REGION="${AWS_REGION:-us-east-2}"
export AWS_PAGER=""

usage() { echo "Usage: $0 <dev|stage|prod>" >&2; exit 1; }
die()   { echo "ERROR: $*" >&2; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "$1 is required"; }
aws_cli() { aws --region "$AWS_REGION" "$@"; }

ssm_exists() { aws_cli ssm get-parameter --name "$1" >/dev/null 2>&1; }
ssm_get() {
  aws_cli ssm get-parameter \
    --name "$1" \
    --query 'Parameter.Value' \
    --output text
}

put_ssm_string() {
  aws_cli ssm put-parameter \
    --name "$1" \
    --type String \
    --tier Standard \
    --value "$2" \
    --overwrite \
    >/dev/null
}

table_exists() {
  aws_cli dynamodb describe-table --table-name "$1" >/dev/null 2>&1
}

cleanup() { rm -f "${TABLE_JSON:-}"; }
trap cleanup EXIT

require aws
require jq

STAGE="${1:-}"
[[ "$STAGE" =~ ^(dev|stage|prod)$ ]] || usage

TABLE_BASE="k9-${STAGE}"
TABLE_NAME="${TABLE_BASE}-companies"
SSM_TABLE="/k9/${STAGE}/data/dynamodb/table"
SSM_STREAM_ARN="/k9/${STAGE}/data/dynamodb/stream/companies"

preflight() {
  local -a issues=()
  local existing_value=""

  if ssm_exists "$SSM_TABLE"; then
    existing_value="$(ssm_get "$SSM_TABLE")"
    issues+=("SSM parameter already exists: $SSM_TABLE = $existing_value")
  fi

  if ssm_exists "$SSM_STREAM_ARN"; then
    existing_value="$(ssm_get "$SSM_STREAM_ARN")"
    issues+=("SSM parameter already exists: $SSM_STREAM_ARN = $existing_value")
  fi

  table_exists "$TABLE_NAME" && \
    issues+=("DynamoDB table already exists: $TABLE_NAME")

  if ((${#issues[@]} > 0)); then
    echo "Preflight failed. Fix these issues, then rerun:" >&2
    printf '  - %s\n' "${issues[@]}" >&2
    exit 1
  fi
}

create_table_payload() {
  jq -n --arg table_name "$TABLE_NAME" '
    {
      TableName: $table_name,
      AttributeDefinitions: [
        { AttributeName: "id", AttributeType: "S" }
      ],
      KeySchema: [
        { AttributeName: "id", KeyType: "HASH" }
      ],
      BillingMode: "PAY_PER_REQUEST",
      StreamSpecification: {
        StreamEnabled: true,
        StreamViewType: "NEW_AND_OLD_IMAGES"
      }
    }
  '
}

preflight

echo "Creating DynamoDB table: $TABLE_NAME"

TABLE_JSON="$(mktemp)"
create_table_payload >"$TABLE_JSON"

aws_cli dynamodb create-table \
  --cli-input-json "file://$TABLE_JSON" \
  >/dev/null

echo "Waiting for table to become ACTIVE"
aws_cli dynamodb wait table-exists --table-name "$TABLE_NAME"

echo "Enabling point-in-time recovery"
aws_cli dynamodb update-continuous-backups \
  --table-name "$TABLE_NAME" \
  --point-in-time-recovery-specification \
    PointInTimeRecoveryEnabled=true,RecoveryPeriodInDays=35 \
  >/dev/null

put_ssm_string "$SSM_TABLE" "$TABLE_BASE"

STREAM_ARN="$(
  aws_cli dynamodb describe-table \
    --table-name "$TABLE_NAME" \
    --query 'Table.LatestStreamArn' \
    --output text
)"

put_ssm_string "$SSM_STREAM_ARN" "$STREAM_ARN"

cat <<EOF

Created DynamoDB table:
  Stage:        $STAGE
  Region:       $AWS_REGION
  TableBase:    $TABLE_BASE
  TableName:    $TABLE_NAME
  PrimaryKey:   id (String)
  BillingMode:  PAY_PER_REQUEST
  StreamView:   NEW_AND_OLD_IMAGES
  StreamArn:    $STREAM_ARN
  PITR:         enabled (35 days)

Stored in SSM:
  $SSM_TABLE = $TABLE_BASE
  $SSM_STREAM_ARN = $STREAM_ARN
EOF