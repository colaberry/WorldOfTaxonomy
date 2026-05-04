#!/usr/bin/env bash
# In-container runner for the wot-ingest Cloud Run Job.
#
# Reads INGEST_TASKS env var (space-separated task IDs from
# scripts/ingest_manifest.json) and runs each task's ordered command list.
#
# Tasks must be idempotent. The runner stops on the first non-zero exit.
#
# Invoked via: gcloud run jobs execute wot-ingest --update-env-vars=INGEST_TASKS="..."
# from scripts/ingest-prod.sh on a developer laptop.

set -euo pipefail

if [ -z "${INGEST_TASKS:-}" ]; then
  echo "ERROR: INGEST_TASKS env var is required (space-separated task IDs)" >&2
  echo "Example: INGEST_TASKS=\"anzsic_2006 soc_2018\"" >&2
  exit 2
fi

MANIFEST="${INGEST_MANIFEST:-scripts/ingest_manifest.json}"
if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: manifest not found at $MANIFEST" >&2
  exit 2
fi

# Use python (already in image) to parse the manifest and dispatch.
# Stays in this single process so we propagate exit codes cleanly.
python3 - <<'PYEOF'
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    manifest_path = Path(os.environ.get("INGEST_MANIFEST", "scripts/ingest_manifest.json"))
    tasks_raw = os.environ["INGEST_TASKS"].split()
    # De-dup while preserving order
    tasks: list[str] = []
    seen: set[str] = set()
    for t in tasks_raw:
        if t not in seen:
            tasks.append(t)
            seen.add(t)

    with manifest_path.open() as f:
        manifest = json.load(f)

    # Strip _doc and any other meta keys (those that start with "_")
    runnable = {k: v for k, v in manifest.items() if not k.startswith("_")}

    unknown = [t for t in tasks if t not in runnable]
    if unknown:
        print("ERROR: unknown task IDs:", file=sys.stderr)
        for t in unknown:
            print(f"  - {t}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Available tasks ({len(runnable)}):", file=sys.stderr)
        for t in sorted(runnable.keys()):
            print(f"  - {t}", file=sys.stderr)
        return 2

    print(f"=== running {len(tasks)} task(s) ===")
    for t in tasks:
        print(f"  - {t} ({len(runnable[t])} command(s))")
    print()

    for task_id in tasks:
        cmds = runnable[task_id]
        print(f"\n>>> task: {task_id}")
        for cmd in cmds:
            print(f"\n$ {cmd}", flush=True)
            r = subprocess.run(cmd, shell=True)
            if r.returncode != 0:
                print(
                    f"\n!! task '{task_id}' FAILED at: {cmd} (exit {r.returncode})",
                    file=sys.stderr,
                )
                return r.returncode

    print(f"\n=== all done: {len(tasks)} task(s) succeeded ===")
    return 0


sys.exit(main())
PYEOF
