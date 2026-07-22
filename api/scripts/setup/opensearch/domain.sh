#!/usr/bin/env bash
set -euo pipefail

# Creates: OpenSearch domain
# Usage: domain.sh <dev|stage|prod>
# Reads from SSM: none
# Writes to SSM:
# - /k9/<stage>/data/opensearch/endpoint
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

domain_exists() {
  aws_cli opensearch describe-domain --domain-name "$1" >/dev/null 2>&1
}

wait_for_domain() {
  local domain_name="$1"
  local deadline=$(( $(date +%s) + 3600 ))

  while true; do
    local processing endpoint
    processing="$(
      aws_cli opensearch describe-domain \
        --domain-name "$domain_name" \
        --query 'DomainStatus.Processing' \
        --output text
    )"
    endpoint="$(
      aws_cli opensearch describe-domain \
        --domain-name "$domain_name" \
        --query 'DomainStatus.Endpoint' \
        --output text
    )"

    if [[ "$processing" == "False" && -n "$endpoint" && "$endpoint" != "None" ]]; then
      return 0
    fi

    (( $(date +%s) < deadline )) || die "Timed out waiting for OpenSearch domain"
    sleep 30
  done
}

main() {
  need aws
  need jq

  local stage="${1:-}"
  validate_stage "$stage"

  local domain_name="k9-${stage}-os"
  local ssm_endpoint="/k9/${stage}/data/opensearch/endpoint"

  ssm_get "$ssm_endpoint" >/dev/null && die "SSM parameter already exists: $ssm_endpoint"
  domain_exists "$domain_name" && die "OpenSearch domain already exists: $domain_name"

  local account_id
  account_id="$(aws_cli sts get-caller-identity --query Account --output text)"
  [[ -n "$account_id" && "$account_id" != "None" ]] || die "Failed to resolve AWS account ID"

  local access_policy
  access_policy="$(
    jq -cn \
      --arg region "$AWS_REGION" \
      --arg account "$account_id" \
      --arg domain "$domain_name" '
      {
        Version: "2012-10-17",
        Statement: [
          {
            Sid: "AllowAccountPrincipalsOnly",
            Effect: "Allow",
            Principal: { AWS: ("arn:aws:iam::" + $account + ":root") },
            Action: "es:*",
            Resource: ("arn:aws:es:" + $region + ":" + $account + ":domain/" + $domain + "/*")
          }
        ]
      }
    '
  )"

  echo "Creating OpenSearch domain: $domain_name"
  aws_cli opensearch create-domain \
    --domain-name "$domain_name" \
    --engine-version OpenSearch_2.19 \
    --cluster-config InstanceType=t3.small.search,InstanceCount=1,DedicatedMasterEnabled=false,ZoneAwarenessEnabled=false \
    --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=10 \
    --domain-endpoint-options EnforceHTTPS=true,TLSSecurityPolicy=Policy-Min-TLS-1-2-2019-07 \
    --node-to-node-encryption-options Enabled=true \
    --encryption-at-rest-options Enabled=true \
    --access-policies "$access_policy" \
    >/dev/null

  echo "Waiting for domain to become active"
  wait_for_domain "$domain_name"

  local endpoint
  endpoint="$(
    aws_cli opensearch describe-domain \
      --domain-name "$domain_name" \
      --query 'DomainStatus.Endpoint' \
      --output text
  )"

  [[ -n "$endpoint" && "$endpoint" != "None" ]] || die "Failed to resolve endpoint"

  local https_endpoint="https://${endpoint}:443"
  ssm_put "$ssm_endpoint" "$https_endpoint"

  cat <<EOF
Created:
  OpenSearch domain: $domain_name
Wrote to SSM:
  $ssm_endpoint = $https_endpoint
EOF
}

main "$@"