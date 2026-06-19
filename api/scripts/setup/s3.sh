#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - Account-regional general-purpose S3 bucket with prefix: k9-<stage>
#   - Actual bucket name: k9-<stage>-<account-id>-<region>-an
# Stores to SSM:
#   - /k9/<stage>/storage/s3/bucket

AWS_REGION="${AWS_REGION:-us-east-2}"
BUCKET_NAMESPACE="account-regional"
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

bucket_exists() {
  aws s3api head-bucket --bucket "$1" >/dev/null 2>&1
}

cleanup() {
  rm -f "${PUBLIC_ACCESS_BLOCK_JSON:-}" "${ENCRYPTION_JSON:-}" "${POLICY_JSON:-}"
}
trap cleanup EXIT

require aws
require jq

STAGE="${1:-}"
[[ "$STAGE" =~ ^(dev|stage|prod)$ ]] || usage

BUCKET_PREFIX="k9-${STAGE}"
SSM_BUCKET="/k9/${STAGE}/storage/s3/bucket"

if ! aws s3api create-bucket help 2>/dev/null | grep -q -- '--bucket-namespace'; then
  die $'Your AWS CLI does not support:\n  aws s3api create-bucket --bucket-namespace\n\nUpdate AWS CLI v2 and rerun.'
fi

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
[[ -n "$ACCOUNT_ID" && "$ACCOUNT_ID" != "None" ]] || die "Failed to resolve AWS account ID."

BUCKET_NAME="${BUCKET_PREFIX}-${ACCOUNT_ID}-${AWS_REGION}-an"
((${#BUCKET_NAME} <= 63)) || die "Bucket name exceeds 63 characters: $BUCKET_NAME"

case "$AWS_REGION" in
  me-south-1|me-central-1)
    die "Account-regional S3 bucket namespace is not supported in $AWS_REGION."
    ;;
esac

preflight() {
  local -a issues=()

  ssm_exists "$SSM_BUCKET" && \
    issues+=("SSM parameter already exists: $SSM_BUCKET")

  bucket_exists "$BUCKET_NAME" && \
    issues+=("S3 bucket already exists or is not accessible: $BUCKET_NAME")

  if ((${#issues[@]} > 0)); then
    echo "Preflight failed. Fix these issues, then rerun:" >&2
    printf '  - %s\n' "${issues[@]}" >&2
    exit 1
  fi
}

create_public_access_block_payload() {
  jq -n '
    {
      BlockPublicAcls: true,
      IgnorePublicAcls: true,
      BlockPublicPolicy: false,
      RestrictPublicBuckets: false
    }
  '
}

create_encryption_payload() {
  jq -n '
    {
      Rules: [
        {
          ApplyServerSideEncryptionByDefault: { SSEAlgorithm: "AES256" },
          BucketKeyEnabled: false
        }
      ]
    }
  '
}

create_policy_payload() {
  jq -n --arg bucket "$BUCKET_NAME" '
    {
      Version: "2012-10-17",
      Statement: [
        {
          Sid: "AllowPublicReadForJxlAndSvgObjectsOnly",
          Effect: "Allow",
          Principal: "*",
          Action: "s3:GetObject",
          Resource: [
            "arn:aws:s3:::\($bucket)/*.jxl",
            "arn:aws:s3:::\($bucket)/*.svg"
          ]
        }
      ]
    }
  '
}

preflight

echo "Creating S3 bucket: $BUCKET_NAME"

if [[ "$AWS_REGION" == "us-east-1" ]]; then
  aws_cli s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --bucket-namespace "$BUCKET_NAMESPACE" \
    >/dev/null
else
  aws_cli s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --bucket-namespace "$BUCKET_NAMESPACE" \
    --create-bucket-configuration "LocationConstraint=$AWS_REGION" \
    >/dev/null
fi

aws_cli s3api put-bucket-ownership-controls \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' \
  >/dev/null

PUBLIC_ACCESS_BLOCK_JSON="$(mktemp)"
create_public_access_block_payload >"$PUBLIC_ACCESS_BLOCK_JSON"

aws_cli s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --public-access-block-configuration "file://$PUBLIC_ACCESS_BLOCK_JSON" \
  >/dev/null

ENCRYPTION_JSON="$(mktemp)"
create_encryption_payload >"$ENCRYPTION_JSON"

aws_cli s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --server-side-encryption-configuration "file://$ENCRYPTION_JSON" \
  >/dev/null

POLICY_JSON="$(mktemp)"
create_policy_payload >"$POLICY_JSON"

aws_cli s3api put-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --policy "file://$POLICY_JSON" \
  >/dev/null

put_ssm_string "$SSM_BUCKET" "$BUCKET_NAME"

cat <<EOF

Created S3 bucket:
  Stage:      $STAGE
  Region:     $AWS_REGION
  BucketName: $BUCKET_NAME

Stored in SSM:
  $SSM_BUCKET
EOF