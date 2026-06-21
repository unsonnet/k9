#!/usr/bin/env bash
set -euo pipefail

# Creates:
#   - OpenSearch domain: k9-<stage>-os (engine OpenSearch_2.19)
#   - OpenSearch index:  k9-<stage>-companies
# Stores to SSM:
#   - /k9/<stage>/data/opensearch/endpoint
#   - /k9/<stage>/data/opensearch/index

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

domain_exists() {
  aws_cli opensearch describe-domain --domain-name "$1" >/dev/null 2>&1
}

cleanup() {
  rm -f \
    "${ACCESS_POLICY_JSON:-}" \
    "${INDEX_JSON:-}" \
    "${RESPONSE_BODY:-}" \
    "${RESPONSE_HEADERS:-}" \
    "${CREDS_JSON:-}"
}
trap cleanup EXIT

require aws
require jq
require curl

STAGE="${1:-}"
[[ "$STAGE" =~ ^(dev|stage|prod)$ ]] || usage

DOMAIN_NAME="k9-${STAGE}-os"
INDEX_BASE="k9-${STAGE}"
INDEX_NAME="${INDEX_BASE}-companies"

SSM_ENDPOINT="/k9/${STAGE}/data/opensearch/endpoint"
SSM_INDEX="/k9/${STAGE}/data/opensearch/index"

if ! curl --help all 2>/dev/null | grep -q -- '--aws-sigv4'; then
  die "curl does not support --aws-sigv4. Update curl before running this script."
fi

if ! aws configure export-credentials --format process >/dev/null 2>&1; then
  die "Your AWS CLI does not support 'aws configure export-credentials'. Update AWS CLI v2."
fi

ACCOUNT_ID="$(
  aws_cli sts get-caller-identity --query Account --output text
)"
[[ -n "$ACCOUNT_ID" && "$ACCOUNT_ID" != "None" ]] || die "Failed to resolve AWS account ID."

create_access_policy() {
  jq -n \
    --arg region "$AWS_REGION" \
    --arg account_id "$ACCOUNT_ID" \
    --arg domain_name "$DOMAIN_NAME" '
    {
      Version: "2012-10-17",
      Statement: [
        {
          Sid: "AllowAccountPrincipalsOnly",
          Effect: "Allow",
          Principal: {
            AWS: "arn:aws:iam::\($account_id):root"
          },
          Action: "es:*",
          Resource: "arn:aws:es:\($region):\($account_id):domain/\($domain_name)/*"
        }
      ]
    }
  '
}

create_index_payload() {
  jq -n '
    {
      settings: {
        index: {
          number_of_shards: 1,
          number_of_replicas: 1
        },
        analysis: {
          char_filter: {
            name_symbols: {
              type: "mapping",
              mappings: [
                "& => and "
              ]
            }
          },
          filter: {
            name_word_delimiter: {
              type: "word_delimiter_graph",
              preserve_original: true,
              generate_word_parts: true,
              generate_number_parts: true,
              catenate_words: true,
              catenate_numbers: true,
              catenate_all: true,
              split_on_case_change: true,
              split_on_numerics: true,
              stem_english_possessive: true
            }
          },
          analyzer: {
            name_text: {
              type: "custom",
              char_filter: ["name_symbols"],
              tokenizer: "standard",
              filter: ["lowercase", "asciifolding"]
            },
            name_wdg: {
              type: "custom",
              char_filter: ["name_symbols"],
              tokenizer: "keyword",
              filter: ["lowercase", "asciifolding", "name_word_delimiter"]
            }
          }
        }
      },
      mappings: {
        dynamic: "strict",
        properties: {
          id: {
            type: "keyword"
          },
          sector: {
            type: "keyword"
          },
          name: {
            type: "text",
            analyzer: "name_text",
            fields: {
              sat: {
                type: "search_as_you_type",
                analyzer: "name_text",
                max_shingle_size: 3
              },
              wdg: {
                type: "text",
                analyzer: "name_wdg"
              }
            }
          },
          logo: {
            type: "keyword",
            index: false
          },
          website: {
            type: "keyword",
            index: false
          },
          locations: {
            properties: {
              street: { type: "keyword" },
              city:   { type: "keyword" },
              state:  { type: "keyword" },
              zip:    { type: "keyword" },
              geo:    { type: "geo_point" }
            }
          }
        }
      }
    }
  '
}

load_cli_credentials() {
  CREDS_JSON="$(mktemp)"
  aws configure export-credentials --format process >"$CREDS_JSON"

  AWS_ACCESS_KEY_ID="$(jq -r '.AccessKeyId // empty' <"$CREDS_JSON")"
  AWS_SECRET_ACCESS_KEY="$(jq -r '.SecretAccessKey // empty' <"$CREDS_JSON")"
  AWS_SESSION_TOKEN="$(jq -r '.SessionToken // empty' <"$CREDS_JSON")"

  [[ -n "$AWS_ACCESS_KEY_ID" ]]     || die "Failed to load AccessKeyId from AWS CLI credentials."
  [[ -n "$AWS_SECRET_ACCESS_KEY" ]] || die "Failed to load SecretAccessKey from AWS CLI credentials."
}

os_put_index() {
  local url="${OS_ENDPOINT}/${INDEX_NAME}"

  RESPONSE_BODY="$(mktemp)"
  RESPONSE_HEADERS="$(mktemp)"

  local -a args=(
    --silent
    --show-error
    --request PUT
    --url "$url"
    --aws-sigv4 "aws:amz:${AWS_REGION}:es"
    --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}"
    --header "content-type: application/json"
    --data-binary "@${INDEX_JSON}"
    --output "$RESPONSE_BODY"
    --dump-header "$RESPONSE_HEADERS"
  )

  [[ -n "${AWS_SESSION_TOKEN:-}" ]] && \
    args+=(--header "x-amz-security-token: ${AWS_SESSION_TOKEN}")

  curl "${args[@]}" >/dev/null

  local status
  status="$(awk 'toupper($1) ~ /^HTTP/ { code=$2 } END { print code }' "$RESPONSE_HEADERS")"

  [[ -n "$status" ]] || die "No HTTP status returned from OpenSearch."

  if (( status >= 300 )); then
    echo "ERROR: OpenSearch index creation failed with HTTP ${status}" >&2
    cat "$RESPONSE_BODY" >&2 || true
    exit 1
  fi
}

wait_for_domain_active() {
  local processing endpoint timeout_at now
  timeout_at=$(( $(date +%s) + 1800 ))

  while true; do
    processing="$(
      aws_cli opensearch describe-domain \
        --domain-name "$DOMAIN_NAME" \
        --query 'DomainStatus.Processing' \
        --output text
    )"

    endpoint="$(
      aws_cli opensearch describe-domain \
        --domain-name "$DOMAIN_NAME" \
        --query 'DomainStatus.Endpoint' \
        --output text
    )"

    if [[ "$processing" == "False" && -n "$endpoint" && "$endpoint" != "None" ]]; then
      break
    fi

    now=$(date +%s)
    (( now < timeout_at )) || die "Timed out waiting for OpenSearch domain to become active."
    sleep 30
  done
}

preflight() {
  local -a issues=()
  local existing=""

  if ! aws_cli sts get-caller-identity >/dev/null 2>&1; then
    issues+=("AWS CLI is not authenticated or cannot call sts:GetCallerIdentity")
  fi

  if ssm_exists "$SSM_ENDPOINT"; then
    existing="$(ssm_get "$SSM_ENDPOINT")"
    issues+=("SSM parameter already exists: $SSM_ENDPOINT = $existing")
  fi

  if ssm_exists "$SSM_INDEX"; then
    existing="$(ssm_get "$SSM_INDEX")"
    issues+=("SSM parameter already exists: $SSM_INDEX = $existing")
  fi

  domain_exists "$DOMAIN_NAME" && \
    issues+=("OpenSearch domain already exists: $DOMAIN_NAME")

  if ((${#issues[@]} > 0)); then
    echo "Preflight failed. Fix these issues, then rerun:" >&2
    printf '  - %s\n' "${issues[@]}" >&2
    exit 1
  fi
}

preflight

echo "Creating OpenSearch domain: $DOMAIN_NAME"

ACCESS_POLICY_JSON="$(mktemp)"
create_access_policy >"$ACCESS_POLICY_JSON"
ACCESS_POLICY_STRING="$(jq -c . <"$ACCESS_POLICY_JSON")"

aws_cli opensearch create-domain \
  --domain-name "$DOMAIN_NAME" \
  --engine-version OpenSearch_2.19 \
  --cluster-config \
    InstanceType=t3.small.search,InstanceCount=1,DedicatedMasterEnabled=false,ZoneAwarenessEnabled=false \
  --ebs-options \
    EBSEnabled=true,VolumeType=gp3,VolumeSize=10 \
  --access-policies "$ACCESS_POLICY_STRING" \
  --domain-endpoint-options \
    EnforceHTTPS=true,TLSSecurityPolicy=Policy-Min-TLS-1-2-2019-07 \
  >/dev/null

echo "Waiting for OpenSearch domain to become active"
wait_for_domain_active

OS_ENDPOINT="$(
  aws_cli opensearch describe-domain \
    --domain-name "$DOMAIN_NAME" \
    --query 'DomainStatus.Endpoint' \
    --output text
)"
[[ -n "$OS_ENDPOINT" && "$OS_ENDPOINT" != "None" ]] || die "Failed to resolve OpenSearch endpoint."
OS_ENDPOINT="https://${OS_ENDPOINT}:443"

load_cli_credentials

echo "Creating OpenSearch index: $INDEX_NAME"

INDEX_JSON="$(mktemp)"
create_index_payload >"$INDEX_JSON"
os_put_index

put_ssm_string "$SSM_ENDPOINT" "$OS_ENDPOINT"
put_ssm_string "$SSM_INDEX" "$INDEX_BASE"

cat <<EOF

Created OpenSearch resources:
  Stage:      $STAGE
  Region:     $AWS_REGION
  DomainName: $DOMAIN_NAME
  Endpoint:   $OS_ENDPOINT
  IndexBase:  $INDEX_BASE
  IndexName:  $INDEX_NAME

Stored in SSM:
  $SSM_ENDPOINT = $OS_ENDPOINT
  $SSM_INDEX    = $INDEX_BASE
EOF