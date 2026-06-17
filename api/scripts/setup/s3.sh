#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - Account-regional general-purpose S3 bucket with prefix: k9-dev
#   - Actual bucket name: k9-dev-<account-id>-<region>-an
#   - Bucket-owner-enforced object ownership / ACLs disabled
#   - SSE-S3 default encryption
#   - Public read only for *.jxl and *.svg objects
#   - No public list/write/delete from this bucket policy
#
# Notes:
#   - Account-regional namespace buckets are supported in all AWS Regions
#     except Middle East (Bahrain) and Middle East (UAE).
#   - If account-level or organization-level S3 Block Public Access has
#     BlockPublicPolicy=true or RestrictPublicBuckets=true, the public-read
#     policy below may be rejected or rendered ineffective.

BUCKET_PREFIX="k9-dev"
AWS_REGION="us-east-2"
BUCKET_NAMESPACE="account-regional"

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
  rm -f "${PUBLIC_ACCESS_BLOCK_JSON:-}" "${ENCRYPTION_JSON:-}" "${POLICY_JSON:-}"
}

trap cleanup EXIT

require aws
require jq

if ! aws s3api create-bucket help 2>/dev/null | grep -q -- '--bucket-namespace'; then
  cat >&2 <<'EOF'
ERROR: Your AWS CLI does not appear to support:
  aws s3api create-bucket --bucket-namespace

Update AWS CLI v2 before running this script.
EOF
  exit 1
fi

ACCOUNT_ID="$(
  aws sts get-caller-identity \
    --query Account \
    --output text
)"

if [[ -z "$ACCOUNT_ID" || "$ACCOUNT_ID" == "None" ]]; then
  echo "ERROR: Failed to resolve AWS account ID." >&2
  exit 1
fi

BUCKET_NAME="${BUCKET_PREFIX}-${ACCOUNT_ID}-${AWS_REGION}-an"

if (( ${#BUCKET_NAME} > 63 )); then
  echo "ERROR: Bucket name exceeds 63 characters: $BUCKET_NAME" >&2
  exit 1
fi

case "$AWS_REGION" in
  me-south-1|me-central-1)
    echo "ERROR: Account-regional S3 bucket namespace is not supported in $AWS_REGION." >&2
    exit 1
    ;;
esac

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
          ApplyServerSideEncryptionByDefault: {
            SSEAlgorithm: "AES256"
          },
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

echo "Checking account-level S3 Block Public Access settings"

ACCOUNT_PUBLIC_ACCESS_BLOCK="$(
  aws s3control get-public-access-block \
    --account-id "$ACCOUNT_ID" \
    --region "$AWS_REGION" \
    --output json 2>/dev/null || true
)"

if [[ -n "$ACCOUNT_PUBLIC_ACCESS_BLOCK" ]]; then
  ACCOUNT_BLOCK_PUBLIC_POLICY="$(
    printf '%s' "$ACCOUNT_PUBLIC_ACCESS_BLOCK" |
      json_get '.PublicAccessBlockConfiguration.BlockPublicPolicy // false'
  )"

  ACCOUNT_RESTRICT_PUBLIC_BUCKETS="$(
    printf '%s' "$ACCOUNT_PUBLIC_ACCESS_BLOCK" |
      json_get '.PublicAccessBlockConfiguration.RestrictPublicBuckets // false'
  )"

  if [[ "$ACCOUNT_BLOCK_PUBLIC_POLICY" == "true" || "$ACCOUNT_RESTRICT_PUBLIC_BUCKETS" == "true" ]]; then
    cat >&2 <<EOF
WARNING: Account-level S3 Block Public Access may prevent public image reads.

Current account-level settings:
  BlockPublicPolicy:     $ACCOUNT_BLOCK_PUBLIC_POLICY
  RestrictPublicBuckets: $ACCOUNT_RESTRICT_PUBLIC_BUCKETS

This script configures bucket-level settings to allow a narrow public-read
bucket policy, but account-level or organization-level settings can still
override bucket-level settings.
EOF
  fi
else
  echo "Account-level S3 Block Public Access settings unavailable or not configured."
fi

echo "Creating S3 bucket: $BUCKET_NAME"

if [[ "$AWS_REGION" == "us-east-1" ]]; then
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --bucket-namespace "$BUCKET_NAMESPACE" \
    --region "$AWS_REGION" \
    >/dev/null
else
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --bucket-namespace "$BUCKET_NAMESPACE" \
    --region "$AWS_REGION" \
    --create-bucket-configuration "LocationConstraint=$AWS_REGION" \
    >/dev/null
fi

echo "Setting object ownership: BucketOwnerEnforced"

aws s3api put-bucket-ownership-controls \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' \
  >/dev/null

echo "Configuring bucket-level S3 Block Public Access"

PUBLIC_ACCESS_BLOCK_JSON="$(mktemp)"
create_public_access_block_payload > "$PUBLIC_ACCESS_BLOCK_JSON"

aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --public-access-block-configuration "file://$PUBLIC_ACCESS_BLOCK_JSON" \
  >/dev/null

echo "Configuring default encryption: SSE-S3"

ENCRYPTION_JSON="$(mktemp)"
create_encryption_payload > "$ENCRYPTION_JSON"

aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --server-side-encryption-configuration "file://$ENCRYPTION_JSON" \
  >/dev/null

echo "Applying bucket policy: public read for .jxl and .svg only"

POLICY_JSON="$(mktemp)"
create_policy_payload > "$POLICY_JSON"

aws s3api put-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --region "$AWS_REGION" \
  --expected-bucket-owner "$ACCOUNT_ID" \
  --policy "file://$POLICY_JSON" \
  >/dev/null

echo "Verifying bucket policy status"

POLICY_STATUS="$(
  aws s3api get-bucket-policy-status \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION" \
    --expected-bucket-owner "$ACCOUNT_ID" \
    --output json 2>/dev/null || true
)"

IS_PUBLIC="$(
  printf '%s' "$POLICY_STATUS" |
    json_get '.PolicyStatus.IsPublic // "unknown"'
)"

cat <<EOF

Created S3 bucket:
  Region:          $AWS_REGION
  Namespace:       $BUCKET_NAMESPACE
  BucketPrefix:    $BUCKET_PREFIX
  BucketName:      $BUCKET_NAME
  AccountId:       $ACCOUNT_ID

Ownership / ACLs:
  ObjectOwnership: BucketOwnerEnforced
  ACLs:            Disabled

Encryption:
  Default: SSE-S3 / AES256

Bucket-level public access block:
  BlockPublicAcls:       true
  IgnorePublicAcls:      true
  BlockPublicPolicy:     false
  RestrictPublicBuckets: false

Bucket policy:
  IsPublic: $IS_PUBLIC

Public access:
  Public bucket listing: No
  Public writes:         No
  Public deletes:        No
  Public reads:
    - Allowed for object keys ending in .jxl
    - Allowed for object keys ending in .svg

Example public image URLs:
  https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/users/<id>/picture.jxl
  https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/companies/<id>/layout.svg
  https://$BUCKET_NAME.s3.$AWS_REGION.amazonaws.com/products/<id>/images/image.jxl

Recommended app env:
  S3_BUCKET_PREFIX=$BUCKET_PREFIX
  S3_BUCKET_NAME=$BUCKET_NAME
  S3_REGION=$AWS_REGION
EOF