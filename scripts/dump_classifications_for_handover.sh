#!/usr/bin/env bash
# Produce a data-only Postgres dump of the classification tables for
# handover to the CI/CD operator who will refresh production.
#
# What is INCLUDED:
#   alembic_version          (schema migration anchor; restore checks)
#   classification_system
#   classification_node
#   equivalence
#   domain_taxonomy
#   node_taxonomy_link
#   country_system_link
#
# What is EXCLUDED (auth + tenancy + leads - production-owned):
#   app_user, api_key, magic_link_token, usage_log, daily_usage,
#   classify_lead, org
#
# Usage:
#   bash scripts/dump_classifications_for_handover.sh
#   bash scripts/dump_classifications_for_handover.sh --output path.dump
#
# The dump is in PostgreSQL custom format (pg_dump -Fc), data-only, with
# --no-owner --no-acl so it restores cleanly into any role layout.
#
# Restore on prod (Option A: tables already exist, replace data):
#   pg_restore --data-only --disable-triggers --no-owner --no-acl \
#     -h <prod-host> -U <prod-user> -d <prod-db> path.dump
#
# Restore on prod (Option B: tables empty, restore schema + data - only
# safe on a fresh DB):
#   pg_restore --no-owner --no-acl \
#     -h <prod-host> -U <prod-user> -d <prod-db> path.dump

set -euo pipefail

CONTAINER="${WOT_PG_CONTAINER:-wot-postgres}"
DUMP_DATE="$(date +%Y-%m-%d)"
OUTPUT="data/wot_classifications_${DUMP_DATE}.dump"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --container) CONTAINER="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "[dump] container '$CONTAINER' is not running." >&2
  echo "[dump] Start with: docker start $CONTAINER" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

TABLES=(
  alembic_version
  classification_system
  classification_node
  equivalence
  domain_taxonomy
  node_taxonomy_link
  country_system_link
)

# Build pg_dump --table args. Each table needs its own -t flag.
TABLE_ARGS=()
for t in "${TABLES[@]}"; do
  TABLE_ARGS+=(-t "$t")
done

echo "[dump] container: $CONTAINER"
echo "[dump] tables:    ${TABLES[*]}"
echo "[dump] output:    $OUTPUT"

docker exec "$CONTAINER" pg_dump \
  -U "$(docker exec "$CONTAINER" printenv POSTGRES_USER)" \
  -d "$(docker exec "$CONTAINER" printenv POSTGRES_DB)" \
  -Fc \
  --data-only \
  --no-owner --no-acl \
  "${TABLE_ARGS[@]}" \
  > "$OUTPUT"

bytes=$(wc -c < "$OUTPUT" | tr -d ' ')
hr_size=$(du -h "$OUTPUT" | cut -f1)
md5_hex=$(md5 -q "$OUTPUT" 2>/dev/null || md5sum "$OUTPUT" | awk '{print $1}')

echo
echo "[dump] wrote $OUTPUT ($hr_size, $bytes bytes)"
echo "[dump] md5 $md5_hex"
echo

echo "[dump] sanity-check counts (live DB):"
docker exec "$CONTAINER" psql -U "$(docker exec "$CONTAINER" printenv POSTGRES_USER)" \
  -d "$(docker exec "$CONTAINER" printenv POSTGRES_DB)" -At -F $'\t' -c "
select 'classification_system', count(*) from classification_system union all
select 'classification_node', count(*) from classification_node union all
select 'classification_node (with description)', count(description) from classification_node union all
select 'equivalence', count(*) from equivalence union all
select 'domain_taxonomy', count(*) from domain_taxonomy union all
select 'node_taxonomy_link', count(*) from node_taxonomy_link union all
select 'country_system_link', count(*) from country_system_link
order by 1;
" | column -t -s $'\t'

echo
echo "[dump] handover artifact ready: $OUTPUT"
