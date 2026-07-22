#!/usr/bin/env bash
set -euo pipefail

# Creates: DynamoDB table
# Usage: dynamodb.sh <dev|stage|prod>
# Reads from SSM: none
# Writes to SSM:
# - /k9/<stage>/data/dynamodb/table
# - /k9/<stage>/data/dynamodb/stream
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

table_exists() {
  aws_cli dynamodb describe-table --table-name "$1" >/dev/null 2>&1
}

enable_pitr() {
  local table_name="$1"
  local attempt

  echo "Enabling point-in-time recovery"

  for attempt in 1 2 3 4 5; do
    if aws_cli dynamodb update-continuous-backups \
      --table-name "$table_name" \
      --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
      >/dev/null 2>&1; then
      return 0
    fi

    (( attempt < 5 )) || die "Failed to enable point-in-time recovery after $attempt attempts"
    sleep 5
  done
}

main() {
  need aws
  need jq

  local stage="${1:-}"
  validate_stage "$stage"

  local table_name="k9-${stage}"
  local ssm_table="/k9/${stage}/data/dynamodb/table"
  local ssm_stream="/k9/${stage}/data/dynamodb/stream"

  ssm_get "$ssm_table" >/dev/null && die "SSM parameter already exists: $ssm_table"
  ssm_get "$ssm_stream" >/dev/null && die "SSM parameter already exists: $ssm_stream"
  table_exists "$table_name" && die "DynamoDB table already exists: $table_name"

  local payload
  payload="$(
    jq -cn --arg name "$table_name" '
      {
        TableName: $name,
        AttributeDefinitions: [
          { AttributeName: "pk", AttributeType: "S" },
          { AttributeName: "sk", AttributeType: "S" }
        ],
        KeySchema: [
          { AttributeName: "pk", KeyType: "HASH" },
          { AttributeName: "sk", KeyType: "RANGE" }
        ],
        BillingMode: "PAY_PER_REQUEST",
        StreamSpecification: {
          StreamEnabled: true,
          StreamViewType: "NEW_AND_OLD_IMAGES"
        },
        SSESpecification: {
          Enabled: true
        },
        DeletionProtectionEnabled: true
      }
    '
  )"

  echo "Creating DynamoDB table: $table_name"
  aws_cli dynamodb create-table --cli-input-json "$payload" >/dev/null

  echo "Waiting for table to become active"
  aws_cli dynamodb wait table-exists --table-name "$table_name"

  enable_pitr "$table_name"

  local stream_arn
  stream_arn="$(
    aws_cli dynamodb describe-table \
      --table-name "$table_name" \
      --query 'Table.LatestStreamArn' \
      --output text
  )"

  [[ -n "$stream_arn" && "$stream_arn" != "None" ]] || die "Failed to resolve stream ARN"

  ssm_put "$ssm_table" "$table_name"
  ssm_put "$ssm_stream" "$stream_arn"

  cat <<EOF
Created:
  DynamoDB table: $table_name
Wrote to SSM:
  $ssm_table = $table_name
  $ssm_stream = $stream_arn
EOF
}

main "$@"