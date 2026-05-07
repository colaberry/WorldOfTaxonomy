#!/usr/bin/env bash
# Apply a delta SQL file to a Postgres database additively.
#
# Usage:
#   PROD_DATABASE_URL='postgres://...' \
#     bash scripts/apply_delta_dump.sh data/wot_delta_2026-05-05_to_2026-05-07.sql [--yes]
#
# The companion to scripts/dump_classifications_delta.py. The dump is
# wrapped in a single BEGIN; ... COMMIT; transaction with ON CONFLICT
# DO UPDATE on every INSERT, so re-applying the same delta is a no-op
# and partial failures roll back automatically.
#
# Behavior:
#   1. Verifies the file exists.
#   2. If --md5 <hex> is supplied, verifies the MD5 against it.
#   3. Echoes the file's preamble (count of systems / nodes / edges).
#   4. Echoes the connection target (host + dbname); pauses for
#      confirmation unless --yes is passed.
#   5. Runs `psql -v ON_ERROR_STOP=1 -f <file>`.
#   6. Runs a verification query: counts systems with source_date
#      matching the dump.

set -euo pipefail

YES_FLAG=0
EXPECTED_MD5=""
DUMP_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y) YES_FLAG=1; shift ;;
    --md5) EXPECTED_MD5="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,25p' "$0"
      exit 0
      ;;
    *)
      if [[ -z "$DUMP_FILE" ]]; then
        DUMP_FILE="$1"
        shift
      else
        echo "[apply-delta] unknown arg: $1" >&2
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$DUMP_FILE" ]]; then
  echo "[apply-delta] missing dump-file argument" >&2
  echo "[apply-delta] usage: PROD_DATABASE_URL='...' $0 path/to/delta.sql [--yes] [--md5 <hex>]" >&2
  exit 2
fi

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "[apply-delta] file not found: $DUMP_FILE" >&2
  exit 1
fi

if [[ -z "${PROD_DATABASE_URL:-}" ]]; then
  echo "[apply-delta] PROD_DATABASE_URL is not set" >&2
  exit 2
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "[apply-delta] psql not found on PATH" >&2
  exit 2
fi

# Compute MD5 (macOS / Linux compatible)
if command -v md5 >/dev/null 2>&1; then
  ACTUAL_MD5=$(md5 -q "$DUMP_FILE")
else
  ACTUAL_MD5=$(md5sum "$DUMP_FILE" | awk '{print $1}')
fi
echo "[apply-delta] file: $DUMP_FILE"
echo "[apply-delta] md5:  $ACTUAL_MD5"

if [[ -n "$EXPECTED_MD5" && "$ACTUAL_MD5" != "$EXPECTED_MD5" ]]; then
  echo "[apply-delta] MD5 mismatch (expected $EXPECTED_MD5)" >&2
  exit 1
fi

# Echo the dump's own header (lines starting with `-- `) so the
# operator can see what's about to land before confirming.
echo
echo "[apply-delta] dump header:"
grep -m 10 -E '^-- ' "$DUMP_FILE" | sed 's/^/    /'
echo

# Show the connection target without leaking credentials.
TARGET_HOST=$(printf '%s' "$PROD_DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
TARGET_DB=$(printf '%s' "$PROD_DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')
echo "[apply-delta] target host: $TARGET_HOST"
echo "[apply-delta] target db:   $TARGET_DB"
echo

if [[ "$YES_FLAG" -ne 1 ]]; then
  read -r -p "[apply-delta] proceed? type 'yes' to apply: " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo "[apply-delta] aborted." >&2
    exit 0
  fi
fi

echo
echo "[apply-delta] applying ..."
psql -v ON_ERROR_STOP=1 "$PROD_DATABASE_URL" -f "$DUMP_FILE"
echo
echo "[apply-delta] applied. running verification query ..."

# Pull the systems list from the dump header so the verification
# query is generic across delta files. Falls back to the row count
# if the header line is absent (older dumps).
SYS_LINE=$(grep -m 1 -E '^-- Systems included' "$DUMP_FILE" || true)
if [[ -n "$SYS_LINE" ]]; then
  SYS_LIST=$(echo "$SYS_LINE" | sed -E "s/.*: //; s/$//")
  # Build a quoted CSV for SQL: 'a','b','c'
  IFS=',' read -ra IDS <<< "$SYS_LIST"
  QUOTED=""
  for raw in "${IDS[@]}"; do
    id=$(echo "$raw" | tr -d ' ')
    [[ -z "$id" ]] && continue
    if [[ -z "$QUOTED" ]]; then
      QUOTED="'$id'"
    else
      QUOTED="$QUOTED,'$id'"
    fi
  done
  echo "[apply-delta] verifying systems: $SYS_LIST"
  psql "$PROD_DATABASE_URL" -At -F $'\t' -c "
    SELECT id, node_count, source_date
    FROM classification_system
    WHERE id IN ($QUOTED)
    ORDER BY id;
  " | column -t -s $'\t'
else
  psql "$PROD_DATABASE_URL" -At -F $'\t' -c "
    SELECT 'classification_system', count(*) FROM classification_system
    UNION ALL
    SELECT 'classification_node', count(*) FROM classification_node
    UNION ALL
    SELECT 'equivalence', count(*) FROM equivalence;
  " | column -t -s $'\t'
fi

echo
echo "[apply-delta] done."
