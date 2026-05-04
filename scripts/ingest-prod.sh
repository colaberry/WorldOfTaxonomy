#!/usr/bin/env bash
# Host-side wrapper to inject data into prod Cloud SQL via the wot-ingest
# Cloud Run Job. The job's container runs scripts/run_ingest_tasks.sh, which
# reads scripts/ingest_manifest.json and executes the requested tasks.
#
# Usage:
#   ./scripts/ingest-prod.sh <task1> [task2 ...]
#
# Examples:
#   ./scripts/ingest-prod.sh anzsic_2006
#   ./scripts/ingest-prod.sh anzsic_2006 soc_2018 mesh icd_11
#   ./scripts/ingest-prod.sh --list             # list all available task IDs
#
# Tasks are idempotent. Re-running is safe. apply_descriptions() only fills
# rows where description IS NULL or empty; structural ingesters use
# INSERT ... ON CONFLICT DO NOTHING.
#
# Required: gcloud authenticated as a principal with run.jobs.run on
# colaberry-wot project.

set -euo pipefail

PROJECT="${WOT_PROJECT:-colaberry-wot}"
REGION="${WOT_REGION:-us-east1}"
JOB="${WOT_INGEST_JOB:-wot-ingest}"
MANIFEST="${INGEST_MANIFEST:-scripts/ingest_manifest.json}"

usage() {
  cat <<EOF
Usage: $0 <task1> [task2 ...]
       $0 --list

Inject data into prod Cloud SQL by running tasks defined in:
  $MANIFEST

The wrapper triggers the Cloud Run Job '$JOB' in $REGION (project $PROJECT)
with INGEST_TASKS=<your task list> and waits for it to complete.

Environment overrides (all optional):
  WOT_PROJECT          GCP project (default: colaberry-wot)
  WOT_REGION           Cloud Run region (default: us-east1)
  WOT_INGEST_JOB       Job name (default: wot-ingest)
  INGEST_MANIFEST      Manifest path (default: scripts/ingest_manifest.json)

See docs/handover/runbooks/ingest-prod.md for the full runbook, including
how to add a new task and how to verify a populated row.
EOF
}

if [ "$#" -lt 1 ]; then
  usage >&2
  exit 1
fi

if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  usage
  exit 0
fi

if [ "$1" = "--list" ]; then
  if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: manifest not found at $MANIFEST" >&2
    exit 2
  fi
  python3 - "$MANIFEST" <<'PYEOF'
import json
import sys
manifest_path = sys.argv[1]
with open(manifest_path) as f:
    m = json.load(f)
tasks = sorted(k for k in m.keys() if not k.startswith("_"))
print(f"Available tasks ({len(tasks)}):")
for t in tasks:
    n = len(m[t])
    print(f"  {t}  ({n} command{'s' if n != 1 else ''})")
PYEOF
  exit 0
fi

# Validate inputs locally before paying for a Cloud Run Job execution.
if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: manifest not found at $MANIFEST" >&2
  exit 2
fi

TASKS="$*"
python3 - "$MANIFEST" "$TASKS" <<'PYEOF'
import json
import sys
manifest_path, tasks_str = sys.argv[1], sys.argv[2]
with open(manifest_path) as f:
    m = json.load(f)
runnable = {k for k in m.keys() if not k.startswith("_")}
unknown = [t for t in tasks_str.split() if t not in runnable]
if unknown:
    print("ERROR: unknown task ID(s):", file=sys.stderr)
    for t in unknown:
        print(f"  - {t}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Run '{sys.argv[0]} --list' to see available tasks.", file=sys.stderr)
    sys.exit(3)
PYEOF

echo "Running ingest tasks against prod ($PROJECT / $REGION):"
for t in $TASKS; do
  echo "  - $t"
done
echo

gcloud run jobs execute "$JOB" \
  --region="$REGION" \
  --project="$PROJECT" \
  --update-env-vars="INGEST_TASKS=$TASKS" \
  --wait

echo
echo "✓ Ingest done."
echo
echo "Spot-check a populated row (example):"
echo "  curl -s https://wot.aixcelerator.ai/api/v1/systems/<system>/nodes/<code> | jq .description"
