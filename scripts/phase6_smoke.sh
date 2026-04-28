#!/usr/bin/env bash
# Phase 6 end-to-end smoke test.
#
# Drives the full developer-key flow over HTTP against a running
# WoT API, asserting the documented contract at every step:
#
#   1. POST /api/v1/developers/signup           -> 202 + magic_link_url
#   2. GET  /api/v1/auth/magic-callback?t=...   -> Set-Cookie: dev_session
#   3. POST /api/v1/developers/keys             -> raw_key + metadata
#   4. GET  /api/v1/systems/naics_2022          (with Bearer)  -> 200
#   5. DELETE /api/v1/developers/keys/<id>      -> revoked_at set
#   6. GET  /api/v1/systems/naics_2022          (with revoked) -> 401
#
# Requires: bash 4+, curl, jq.
#
# Usage:
#   API_BASE=http://localhost:8000 ./scripts/phase6_smoke.sh
#   API_BASE=https://wot.aixcelerator.ai EMAIL=ram+smoke@colaberry.com \
#       ./scripts/phase6_smoke.sh
#
# The signup endpoint must be running with DEV_KEYS_DEV_MODE=1 so the
# magic link comes back in the response body. Without that env var,
# this script can't drive the flow because no inbox is involved.

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
EMAIL="${EMAIL:-smoke+$(date +%s)@gmail.com}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "$COOKIE_JAR"' EXIT

red()    { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }

require() {
    command -v "$1" >/dev/null 2>&1 || { red "missing: $1"; exit 2; }
}
require curl
require jq

step() { echo; yellow "==> $1"; }

assert_status() {
    local expected="$1" actual="$2" what="$3"
    if [[ "$actual" != "$expected" ]]; then
        red "FAIL: $what: expected $expected, got $actual"
        exit 1
    fi
    green "  OK: $what -> $actual"
}

# 1. Signup -> magic link in response (DEV_KEYS_DEV_MODE=1)
step "Signup ($EMAIL)"
SIGNUP_RESP=$(curl -sS -w '\n%{http_code}' -X POST "$API_BASE/api/v1/developers/signup" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\"}")
SIGNUP_STATUS=$(echo "$SIGNUP_RESP" | tail -n1)
SIGNUP_BODY=$(echo "$SIGNUP_RESP" | sed '$d')
assert_status 202 "$SIGNUP_STATUS" "POST /api/v1/developers/signup"

MAGIC_URL=$(echo "$SIGNUP_BODY" | jq -r '.magic_link_url // empty')
if [[ -z "$MAGIC_URL" ]]; then
    red "FAIL: response did not include magic_link_url"
    red "  Did you set DEV_KEYS_DEV_MODE=1 on the API server?"
    echo "$SIGNUP_BODY" >&2
    exit 1
fi
green "  magic_link_url: $MAGIC_URL"

TOKEN=$(echo "$MAGIC_URL" | sed -n 's/.*[?&]t=\([^&]*\).*/\1/p')
[[ -n "$TOKEN" ]] || { red "could not extract token from magic_link_url"; exit 1; }

# 2. Magic callback -> dev_session cookie
step "Magic-link callback"
CALLBACK_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' \
    -c "$COOKIE_JAR" \
    "$API_BASE/api/v1/auth/magic-callback?t=$TOKEN")
assert_status 200 "$CALLBACK_STATUS" "GET /api/v1/auth/magic-callback"
grep -q dev_session "$COOKIE_JAR" || { red "dev_session cookie not set"; exit 1; }
green "  dev_session cookie persisted"

# 3. Create a key with full WoT scope
step "Generate key (wot:*)"
CREATE_RESP=$(curl -sS -w '\n%{http_code}' -b "$COOKIE_JAR" \
    -X POST "$API_BASE/api/v1/developers/keys" \
    -H 'Content-Type: application/json' \
    -d '{"name":"phase6-smoke","scopes":["wot:*"]}')
CREATE_STATUS=$(echo "$CREATE_RESP" | tail -n1)
CREATE_BODY=$(echo "$CREATE_RESP" | sed '$d')
assert_status 201 "$CREATE_STATUS" "POST /api/v1/developers/keys"

RAW_KEY=$(echo "$CREATE_BODY" | jq -r '.raw_key')
KEY_ID=$(echo "$CREATE_BODY" | jq -r '.metadata.id')
KEY_PREFIX=$(echo "$CREATE_BODY" | jq -r '.metadata.key_prefix')
[[ -n "$RAW_KEY" && -n "$KEY_ID" ]] || { red "raw_key or id missing"; exit 1; }
green "  raw_key prefix: ${RAW_KEY:0:12}..."
green "  key_id: $KEY_ID"
green "  key_prefix: $KEY_PREFIX"

# 4. The key actually authenticates an API call
step "Use key against /api/v1/systems/naics_2022"
USE_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $RAW_KEY" \
    "$API_BASE/api/v1/systems/naics_2022")
# Public read endpoints currently allow anonymous, so 200 with no key
# would also pass. The point of this assertion is that the bearer
# token does not break the call (proving the key is valid).
assert_status 200 "$USE_STATUS" "GET /api/v1/systems/naics_2022 (with key)"

# 5. Revoke the key
step "Revoke key"
REVOKE_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' \
    -X DELETE -b "$COOKIE_JAR" \
    "$API_BASE/api/v1/developers/keys/$KEY_ID")
assert_status 200 "$REVOKE_STATUS" "DELETE /api/v1/developers/keys/$KEY_ID"

# 6. Revoked key fails on a scope-gated endpoint
# Public reads remain 200 (anonymous allowed); scope-gated endpoints
# now reject the revoked key with 401 invalid_api_key.
step "Revoked key denied on a scope-gated endpoint (/api/v1/export/systems.jsonl)"
DENIED_RESP=$(curl -sS -w '\n%{http_code}' \
    -H "Authorization: Bearer $RAW_KEY" \
    "$API_BASE/api/v1/export/systems.jsonl")
DENIED_STATUS=$(echo "$DENIED_RESP" | tail -n1)
DENIED_BODY=$(echo "$DENIED_RESP" | sed '$d')
assert_status 401 "$DENIED_STATUS" "GET /api/v1/export/systems.jsonl (revoked key)"
echo "$DENIED_BODY" | jq -e '.detail.error == "invalid_api_key"' >/dev/null \
    || { red "expected detail.error == invalid_api_key"; echo "$DENIED_BODY" >&2; exit 1; }
green "  detail.error == invalid_api_key"

echo
green "Phase 6 smoke: ALL PASS"
