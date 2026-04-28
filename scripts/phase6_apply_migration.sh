#!/usr/bin/env bash
# Apply migration 003 (Phase 6 developer-key system) with safety checks.
#
# Runs three phases:
#   1. PRE-CHECK: verify connectivity, capture row counts, confirm
#      a 003-shaped migration has not already partially landed.
#   2. DRY RUN:   apply the migration inside `BEGIN; ... ROLLBACK;`
#      so any DDL or constraint failure surfaces before touching the
#      committed schema.
#   3. APPLY:     `psql --single-transaction -v ON_ERROR_STOP=1`
#      with backup-pointer hint and post-migration verification.
#
# Usage:
#   # Local Docker dev DB:
#   ./scripts/phase6_apply_migration.sh \
#       --conn 'postgresql://wot:wot@localhost:5432/worldoftaxanomy'
#
#   # Cloud SQL prod (deploy engineer):
#   ./scripts/phase6_apply_migration.sh \
#       --conn "$(gcloud sql instances describe wot-prod \
#                 --format='get(connectionName)')" \
#       --gcloud-sql-instance wot-prod
#
# Requires: bash 4+, psql >=14, jq.

set -euo pipefail

MIGRATION_FILE="$(cd "$(dirname "$0")/.." && pwd)/world_of_taxonomy/migrations/003_phase6_developer_keys.sql"
[[ -f "$MIGRATION_FILE" ]] || { echo "missing migration: $MIGRATION_FILE" >&2; exit 1; }

CONN_STRING=""
GCLOUD_INSTANCE=""
SKIP_DRY_RUN=0
ASSUME_YES=0

usage() {
    cat <<EOF
Usage: $0 --conn CONNECTION [--gcloud-sql-instance NAME] [--skip-dry-run] [-y]

  --conn STR              Postgres connection string (libpq format)
  --gcloud-sql-instance N Cloud SQL instance name (annotates output, no behavior change)
  --skip-dry-run          Skip the BEGIN/ROLLBACK preview (NOT recommended)
  -y                      Skip the confirm prompt before APPLY

Environment vars:
  PGPASSWORD              Used by psql if your --conn omits the password.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --conn)                CONN_STRING="$2"; shift 2 ;;
        --gcloud-sql-instance) GCLOUD_INSTANCE="$2"; shift 2 ;;
        --skip-dry-run)        SKIP_DRY_RUN=1; shift ;;
        -y)                    ASSUME_YES=1; shift ;;
        -h|--help)             usage; exit 0 ;;
        *)                     echo "unknown arg: $1" >&2; usage; exit 2 ;;
    esac
done

[[ -n "$CONN_STRING" ]] || { usage; exit 2; }

red()    { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
step()   { echo; yellow "==> $1"; }

PSQL="psql -v ON_ERROR_STOP=1"

# ── Phase 1: pre-check ──────────────────────────────────────────────
step "PRE-CHECK"
[[ -n "$GCLOUD_INSTANCE" ]] && yellow "  target Cloud SQL instance: $GCLOUD_INSTANCE"

if ! $PSQL "$CONN_STRING" -tAc 'SELECT 1' >/dev/null; then
    red "FAIL: cannot connect to database"
    exit 1
fi
green "  connectivity: OK"

PRE_COUNTS=$($PSQL "$CONN_STRING" -tAc "
  SELECT format(
    'app_user=%s api_key=%s org=%s',
    (SELECT count(*) FROM app_user),
    (SELECT count(*) FROM api_key),
    (SELECT to_regclass('public.org') IS NULL)
  )
")
green "  pre-counts: $PRE_COUNTS"

ALREADY_APPLIED=$($PSQL "$CONN_STRING" -tAc "
  SELECT bool_and(c IS NOT NULL) FROM (
    SELECT to_regclass('public.org')              AS c UNION ALL
    SELECT to_regclass('public.magic_link_token') AS c
  ) sub
")
if [[ "$ALREADY_APPLIED" == "t" ]]; then
    yellow "  org and magic_link_token already exist - migration appears applied."
    yellow "  (re-applying is safe due to IF NOT EXISTS guards, but unusual)"
fi

# ── Phase 2: dry run ────────────────────────────────────────────────
if [[ "$SKIP_DRY_RUN" == "0" ]]; then
    step "DRY RUN (BEGIN; <migration>; ROLLBACK;)"
    DRY_RUN_FILE="$(mktemp).sql"
    trap 'rm -f "$DRY_RUN_FILE"' EXIT
    {
        echo "BEGIN;"
        cat "$MIGRATION_FILE"
        echo
        echo "SELECT 'DRY-RUN OK' AS result;"
        echo "ROLLBACK;"
    } > "$DRY_RUN_FILE"

    if $PSQL "$CONN_STRING" -f "$DRY_RUN_FILE" >/dev/null; then
        green "  dry run applied cleanly and rolled back"
    else
        red "FAIL: migration errored during dry run; aborting before APPLY."
        exit 1
    fi
else
    yellow "  --skip-dry-run set; skipping preview."
fi

# ── Phase 3: confirm + apply ────────────────────────────────────────
step "APPLY"
if [[ "$ASSUME_YES" == "0" ]]; then
    yellow "About to commit migration 003 to:"
    yellow "  $CONN_STRING"
    [[ -n "$GCLOUD_INSTANCE" ]] && yellow "  Cloud SQL instance: $GCLOUD_INSTANCE"
    read -r -p "Type 'apply' to continue: " CONFIRM
    [[ "$CONFIRM" == "apply" ]] || { red "aborted"; exit 1; }
fi

if [[ -n "$GCLOUD_INSTANCE" ]]; then
    yellow "  Cloud SQL has automatic backups; rollback path is point-in-time"
    yellow "  recovery via:  gcloud sql backups restore --instance=$GCLOUD_INSTANCE"
fi

$PSQL "$CONN_STRING" --single-transaction -f "$MIGRATION_FILE"
green "  migration committed"

# ── Phase 4: verify ─────────────────────────────────────────────────
step "VERIFY"
POST_COUNTS=$($PSQL "$CONN_STRING" -tAc "
  SELECT format(
    'app_user=%s (org_id NOT NULL ok=%s) api_key=%s (scopes NOT NULL ok=%s) org=%s magic_link_token=%s',
    (SELECT count(*) FROM app_user),
    (SELECT bool_and(org_id IS NOT NULL) FROM app_user),
    (SELECT count(*) FROM api_key),
    (SELECT bool_and(scopes IS NOT NULL) FROM api_key),
    (SELECT count(*) FROM org),
    (SELECT count(*) FROM magic_link_token)
  )
")
green "  post-state: $POST_COUNTS"

ORG_BREAKDOWN=$($PSQL "$CONN_STRING" -tAc "
  SELECT string_agg(format('%s=%s', kind, c), ' ')
  FROM (SELECT kind, count(*) AS c FROM org GROUP BY kind) sub
")
[[ -n "$ORG_BREAKDOWN" ]] && green "  org by kind: $ORG_BREAKDOWN"

ROLE_BREAKDOWN=$($PSQL "$CONN_STRING" -tAc "
  SELECT string_agg(format('%s=%s', role, c), ' ')
  FROM (SELECT role, count(*) AS c FROM app_user GROUP BY role) sub
")
[[ -n "$ROLE_BREAKDOWN" ]] && green "  app_user by role: $ROLE_BREAKDOWN"

LEGACY_KEYS=$($PSQL "$CONN_STRING" -tAc "
  SELECT count(*) FROM api_key WHERE 'wot:*' = ANY(scopes)
")
green "  api_key rows backfilled with scopes=['wot:*']: $LEGACY_KEYS"

green ""
green "Phase 6 migration: COMPLETE on this database."
