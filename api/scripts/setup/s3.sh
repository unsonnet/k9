#!/usr/bin/env bash
set -euo pipefail

# Creates: S3 bucket
# Usage: s3.sh <dev|stage|prod>
# Reads from SSM: none
# Writes to SSM:
# - /k9/<stage>/storage/s3/bucket
# Rerun: yes

AWS_REGION="${AWS_REGION:-us-east-2}"
BUCKET_NAMESPACE="account-regional"
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

ssm_put() {
  aws_cli ssm put-parameter \
    --name "$1" \
    --type String \
    --tier Standard \
    --value "$2" \
    --overwrite \
    >/dev/null
}

bucket_exists() {
  aws s3api head-bucket --bucket "$1" >/dev/null 2>&1
}

main() {
  need aws
  need jq

  local stage="${1:-}"
  validate_stage "$stage"

  case "$AWS_REGION" in
    me-south-1|me-central-1)
      die "Account-regional buckets are not supported in $AWS_REGION"
      ;;
  esac

  if ! aws s3api create-bucket help 2>/dev/null | grep -q -- '--bucket-namespace'; then
    die "AWS CLI v2 with --bucket-namespace support is required"
  fi

  local account_id
  account_id="$(aws sts get-caller-identity --query Account --output text)"
  [[ -n "$account_id" && "$account_id" != "None" ]] || die "Failed to resolve AWS account ID"

  local bucket_name="k9-${stage}-${account_id}-${AWS_REGION}-an"
  local ssm_bucket="/k9/${stage}/storage/s3/bucket"

  ((${#bucket_name} <= 63)) || die "Bucket name exceeds 63 characters: $bucket_name"

  if bucket_exists "$bucket_name"; then
    echo "Bucket already exists: $bucket_name"
  else
    echo "Creating S3 bucket: $bucket_name"
    if [[ "$AWS_REGION" == "us-east-1" ]]; then
      aws_cli s3api create-bucket \
        --bucket "$bucket_name" \
        --bucket-namespace "$BUCKET_NAMESPACE" \
        >/dev/null
    else
      aws_cli s3api create-bucket \
        --bucket "$bucket_name" \
        --bucket-namespace "$BUCKET_NAMESPACE" \
        --create-bucket-configuration "LocationConstraint=${AWS_REGION}" \
        >/dev/null
    fi
  fi

  echo "Applying ownership controls"
  aws_cli s3api put-bucket-ownership-controls \
    --bucket "$bucket_name" \
    --expected-bucket-owner "$account_id" \
    --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]' \
    >/dev/null

  echo "Applying public access block"
  aws_cli s3api put-public-access-block \
    --bucket "$bucket_name" \
    --expected-bucket-owner "$account_id" \
    --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false \
    >/dev/null

  echo "Applying encryption"
  aws_cli s3api put-bucket-encryption \
    --bucket "$bucket_name" \
    --expected-bucket-owner "$account_id" \
    --server-side-encryption-configuration \
      '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":false}]}' \
    >/dev/null

  echo "Applying bucket policy"
  aws_cli s3api put-bucket-policy \
    --bucket "$bucket_name" \
    --expected-bucket-owner "$account_id" \
    --policy "$(
      jq -cn --arg bucket "$bucket_name" '
        {
          Version: "2012-10-17",
          Statement: [
            {
              Sid: "AllowPublicReadForJxlAndSvg",
              Effect: "Allow",
              Principal: "*",
              Action: ["s3:GetObject"],
              Resource: [
                ("arn:aws:s3:::\($bucket)/*.jxl"),
                ("arn:aws:s3:::\($bucket)/*.svg")
              ]
            }
          ]
        }
      '
    )" \
    >/dev/null

  ssm_put "$ssm_bucket" "$bucket_name"

  cat <<EOF
Ready:
  S3 bucket: $bucket_name
Wrote to SSM:
  $ssm_bucket = $bucket_name
EOF
}

main "$@"