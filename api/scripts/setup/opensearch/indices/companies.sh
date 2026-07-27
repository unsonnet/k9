#!/usr/bin/env bash
set -euo pipefail

# Creates: OpenSearch companies index
# Usage: companies.sh <dev|stage|prod> [--refresh]
# Reads from SSM:
# - /k9/<stage>/data/opensearch/endpoint
# Writes to SSM:
# - /k9/<stage>/data/opensearch/index/companies
# Rerun: yes, with --refresh

AWS_REGION="${AWS_REGION:-us-east-2}"
export AWS_PAGER=""

response_file=""
trap 'rm -f "${response_file:-}"' EXIT

usage() {
  echo "Usage: $0 <dev|stage|prod> [--refresh]" >&2
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

load_sigv4_creds() {
  local creds_json
  creds_json="$(aws configure export-credentials --format process)"

  AWS_ACCESS_KEY_ID="$(jq -r '.AccessKeyId // empty' <<<"$creds_json")"
  AWS_SECRET_ACCESS_KEY="$(jq -r '.SecretAccessKey // empty' <<<"$creds_json")"
  AWS_SESSION_TOKEN="$(jq -r '.SessionToken // empty' <<<"$creds_json")"

  [[ -n "$AWS_ACCESS_KEY_ID" ]] || die "Failed to load AWS access key"
  [[ -n "$AWS_SECRET_ACCESS_KEY" ]] || die "Failed to load AWS secret key"
}

os_request() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local response_file="$4"

  local -a args=(
    --silent
    --show-error
    --write-out '%{http_code}'
    --output "$response_file"
    --url "$url"
    --aws-sigv4 "aws:amz:${AWS_REGION}:es"
    --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}"
  )

  if [[ "$method" == "HEAD" ]]; then
    args+=(--head)
  else
    args+=(--request "$method")
  fi

  [[ -n "${AWS_SESSION_TOKEN:-}" ]] && args+=(--header "x-amz-security-token: ${AWS_SESSION_TOKEN}")
  [[ -n "$body" ]] && args+=(--header 'content-type: application/json' --data-binary "$body")

  curl "${args[@]}"
}

main() {
  need aws
  need jq
  need curl

  local stage="${1:-}"
  local refresh_flag="${2:-}"
  local refresh=false

  validate_stage "$stage"
  [[ -z "$refresh_flag" || "$refresh_flag" == "--refresh" ]] || usage
  [[ "$refresh_flag" == "--refresh" ]] && refresh=true

  curl --help all 2>/dev/null | grep -q -- '--aws-sigv4' || die "curl with --aws-sigv4 support is required"
  aws configure export-credentials --format process >/dev/null 2>&1 || die "AWS CLI v2 export-credentials support is required"

  local index_name="k9-${stage}-companies"
  local ssm_endpoint="/k9/${stage}/data/opensearch/endpoint"
  local ssm_index="/k9/${stage}/data/opensearch/index/companies"
  local os_endpoint

  os_endpoint="$(ssm_get "$ssm_endpoint")" || die "Missing SSM parameter: $ssm_endpoint"
  load_sigv4_creds

  response_file="$(mktemp)"

  local status
  status="$(os_request HEAD "${os_endpoint}/${index_name}" "" "$response_file")"

  if [[ "$status" =~ ^2 ]]; then
    $refresh || die "Index already exists. Rerun with --refresh."

    echo "Deleting OpenSearch index: $index_name"
    status="$(os_request DELETE "${os_endpoint}/${index_name}" "" "$response_file")"
    [[ "$status" =~ ^2 ]] || { cat "$response_file" >&2; die "Failed to delete index (HTTP $status)"; }
  elif [[ "$status" != "404" ]]; then
    cat "$response_file" >&2
    die "Unexpected response checking index (HTTP $status)"
  fi

  local payload
  payload="$(
    jq -cn '
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
                mappings: ["& => and "]
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
            id: { type: "keyword" },
            type: { type: "keyword" },
            sector: { type: "keyword" },
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
            logo: { type: "keyword", index: false },
            website: { type: "keyword", index: false },
            "$location": {
              properties: {
                id: { type: "keyword" },
                type: { type: "keyword" },
                street: { type: "keyword" },
                city: { type: "keyword" },
                state: { type: "keyword" },
                zip: { type: "keyword" },
                geo: { type: "geo_point" }
              }
            },
            "$contact": {
              properties: {
                id: { type: "keyword" },
                type: { type: "keyword" },
                name: { type: "keyword" },
                title: { type: "keyword" },
                profile: { type: "keyword", index: false },
                email: { type: "keyword" },
                phone: { type: "keyword" }
              }
            }
          }
        }
      }
    '
  )"

  echo "Creating OpenSearch index: $index_name"
  status="$(os_request PUT "${os_endpoint}/${index_name}" "$payload" "$response_file")"
  [[ "$status" =~ ^2 ]] || { cat "$response_file" >&2; die "Failed to create index (HTTP $status)"; }

  ssm_put "$ssm_index" "$index_name"

  cat <<EOF
Ready:
  OpenSearch index: $index_name
Wrote to SSM:
  $ssm_index = $index_name
EOF
}

main "$@"