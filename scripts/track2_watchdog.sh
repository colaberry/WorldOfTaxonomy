#!/usr/bin/env bash
# Watchdog for the Track 2 verified-LLM pipeline. Auto-restarts the
# backfill_llm_verified process if it stalls (no cache growth within
# STALL_SEC) or dies unexpectedly.
#
# Long-lived asyncio HTTP clients can wedge after transient network
# blips: the connector pool caches a DNS or TLS failure and the
# 3-attempt retry loop keeps hitting the same cached error forever
# even after the host network recovers. Direct curl from the same
# shell works fine; only the wedged process is broken. The cure is
# a fresh process. Cache is durable; restarts are free.
#
# Usage:
#   bash scripts/track2_watchdog.sh                                    # CPC, defaults
#   SYSTEM=unspsc_v24 bash scripts/track2_watchdog.sh                   # different system
#   STALL_SEC=900 CHECK_SEC=60 bash scripts/track2_watchdog.sh          # tighter loop
#   CONCURRENCY=24 VERIFIER_MODEL=gpt-oss:20b bash scripts/track2_watchdog.sh
#
# Env (with defaults):
#   SYSTEM           target system_id (default: patent_cpc)
#   CONCURRENCY      passed through to backfill_llm_verified (default: 12)
#   VERIFIER_MODEL   passed through to backfill_llm_verified (default: unset, uses gpt-oss:120b)
#   LIMIT            passed through to backfill_llm_verified (default: 0, full system)
#   STALL_SEC        kill+restart if cache hasn't grown in this many seconds (default: 1800 = 30 min)
#   CHECK_SEC        polling interval (default: 300 = 5 min)
#   LOG_DIR          where to write logs (default: /tmp)
#   PYTHON_BIN       Python interpreter (default: /usr/bin/python3 - the macOS system Python that has the project deps)
#
# Run detached:
#   nohup bash scripts/track2_watchdog.sh > /tmp/cpc_watchdog.log 2>&1 &

set -uo pipefail

SYSTEM="${SYSTEM:-patent_cpc}"
CONCURRENCY="${CONCURRENCY:-12}"
LIMIT="${LIMIT:-0}"
STALL_SEC="${STALL_SEC:-1800}"
CHECK_SEC="${CHECK_SEC:-300}"
LOG_DIR="${LOG_DIR:-/tmp}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
CACHE_FILE="data/llm_verified/${SYSTEM}.jsonl"

WATCHDOG_LOG="${LOG_DIR}/track2_watchdog_${SYSTEM}.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$WATCHDOG_LOG"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

start_pipeline() {
  if [ -z "${OLLAMA_API_KEY:-}" ] && [ -z "${OPENROUTER_API_KEY:-}" ]; then
    log "ERROR: no LLM provider configured (OLLAMA_API_KEY or OPENROUTER_API_KEY)"
    return 1
  fi
  local pipeline_log="${LOG_DIR}/track2_${SYSTEM}_$(date +%Y%m%d_%H%M%S).log"
  local limit_arg=""
  if [ "${LIMIT}" -gt 0 ]; then
    limit_arg="--limit ${LIMIT}"
  fi
  log "Starting pipeline: SYSTEM=${SYSTEM} CONCURRENCY=${CONCURRENCY} VERIFIER_MODEL='${VERIFIER_MODEL:-default}' LOG=${pipeline_log}"
  nohup "${PYTHON_BIN}" -m scripts.backfill_llm_verified \
    --systems "${SYSTEM}" \
    --concurrency "${CONCURRENCY}" \
    ${limit_arg} \
    >> "${pipeline_log}" 2>&1 &
  PIPELINE_PID=$!
  echo "${PIPELINE_PID}" > "/tmp/track2_${SYSTEM}.pid"
  log "  pipeline PID: ${PIPELINE_PID}"
  sleep 5
}

is_pipeline_alive() {
  local pid="$(cat /tmp/track2_${SYSTEM}.pid 2>/dev/null || echo)"
  [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null
}

kill_pipeline() {
  log "Killing pipeline + any stragglers"
  pkill -f "backfill_llm_verified.*${SYSTEM}" 2>/dev/null || true
  sleep 5
  pkill -9 -f "backfill_llm_verified.*${SYSTEM}" 2>/dev/null || true
  sleep 2
}

cache_size() {
  if [ -f "${CACHE_FILE}" ]; then
    wc -l < "${CACHE_FILE}" | tr -d ' '
  else
    echo 0
  fi
}

main() {
  log "Watchdog starting: SYSTEM=${SYSTEM} STALL_SEC=${STALL_SEC} CHECK_SEC=${CHECK_SEC}"

  # Adopt or start
  if pgrep -f "backfill_llm_verified.*${SYSTEM}" >/dev/null 2>&1; then
    local existing_pid
    existing_pid=$(pgrep -f "backfill_llm_verified.*${SYSTEM}" | head -1)
    log "  adopting existing pipeline (PID ${existing_pid})"
    echo "${existing_pid}" > "/tmp/track2_${SYSTEM}.pid"
  else
    start_pipeline || exit 1
  fi

  local last_size
  local last_growth_ts
  last_size=$(cache_size)
  last_growth_ts=$(date +%s)
  log "  initial cache: ${last_size} rows"

  while true; do
    sleep "${CHECK_SEC}"

    if ! is_pipeline_alive; then
      log "Pipeline died unexpectedly; restarting"
      start_pipeline || exit 1
      last_size=$(cache_size)
      last_growth_ts=$(date +%s)
      continue
    fi

    local cur_size
    cur_size=$(cache_size)
    local now_ts
    now_ts=$(date +%s)

    if [ "${cur_size}" -gt "${last_size}" ]; then
      local delta=$((cur_size - last_size))
      local secs=$((now_ts - last_growth_ts))
      log "Healthy: cache ${last_size} -> ${cur_size} (+${delta} in ${secs}s)"
      last_size=${cur_size}
      last_growth_ts=${now_ts}
    else
      local stalled_for=$((now_ts - last_growth_ts))
      log "No cache growth for ${stalled_for}s (cache stays at ${cur_size})"
      if [ "${stalled_for}" -ge "${STALL_SEC}" ]; then
        log "STALLED >= ${STALL_SEC}s - killing and restarting"
        kill_pipeline
        start_pipeline || exit 1
        last_size=$(cache_size)
        last_growth_ts=$(date +%s)
      fi
    fi
  done
}

main
