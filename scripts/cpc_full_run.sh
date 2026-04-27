#!/usr/bin/env bash
# Track 2 verified-LLM full run for patent_cpc.
#
# Pilot established a 98% yes-rate at 500 rows; full target is the
# remaining ~211K empty rows. The Track 2 cache makes resumption
# automatic: rerunning this script after an interruption picks up
# where it left off (cached codes are skipped, only new ones go to
# the LLM + verifier).
#
# Prereqs:
#   - DATABASE_URL set (Postgres reachable, schema migrated)
#   - OLLAMA_API_KEY set (Ollama Cloud, gpt-oss:120b)
#   - No other Track 2 process running against patent_cpc
#
# Usage:
#   bash scripts/cpc_full_run.sh                       # full run, conc 12, both hops on gpt-oss:120b
#   CONCURRENCY=8 bash scripts/cpc_full_run.sh         # throttle to 8
#   LIMIT=5000 bash scripts/cpc_full_run.sh            # cap this invocation
#   VERIFIER_MODEL=gpt-oss:20b bash ...                # use smaller verifier (~2x throughput)

set -euo pipefail

CONCURRENCY="${CONCURRENCY:-12}"
LIMIT="${LIMIT:-0}"
LOG_DIR="${LOG_DIR:-/tmp}"
LOG_FILE="${LOG_DIR}/cpc_full_run_$(date +%Y%m%d_%H%M%S).log"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL not set. Source .env first." >&2
  exit 1
fi
if [ -z "${OLLAMA_API_KEY:-}" ] && [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: no LLM provider configured (OLLAMA_API_KEY or OPENROUTER_API_KEY)." >&2
  exit 1
fi
if pgrep -f "backfill_llm_verified.*patent_cpc" >/dev/null; then
  echo "ERROR: another Track 2 patent_cpc process is already running." >&2
  exit 1
fi

LIMIT_ARG=""
if [ "${LIMIT}" -gt 0 ]; then
  LIMIT_ARG="--limit ${LIMIT}"
fi

echo "Starting CPC Track 2 full run"
echo "  concurrency:    ${CONCURRENCY}"
echo "  limit:          ${LIMIT:-(none, full system)}"
echo "  verifier model: ${VERIFIER_MODEL:-(default gpt-oss:120b)}"
echo "  log:            ${LOG_FILE}"
echo

VERIFIER_MODEL="${VERIFIER_MODEL:-}" PYTHONPATH=. python3 -m scripts.backfill_llm_verified \
  --systems patent_cpc \
  --concurrency "${CONCURRENCY}" \
  ${LIMIT_ARG} \
  2>&1 | tee "${LOG_FILE}"
