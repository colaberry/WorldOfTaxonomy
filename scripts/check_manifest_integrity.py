#!/usr/bin/env python3
"""Validate scripts/ingest_manifest.json structure + script existence.

Runs in CI to catch typos, missing scripts, or malformed manifest entries
before they hit prod. Mirrors the spirit of
scripts/check_static_content_integrity.py (added in PR #163).

Exits 0 on success, non-zero on any validation error.

Invariants enforced:
1. Manifest is a JSON object (mapping of task_id -> list of commands).
2. Keys starting with '_' are treated as documentation (e.g. '_doc') and
   skipped. All other keys are runnable task IDs.
3. Task IDs are non-empty, lowercase-with-underscores, no whitespace.
4. Each task's value is a non-empty list of non-empty strings.
5. Every 'python scripts/X.py' command references a file that exists in
   the repo. Other shell commands (e.g. 'python -m world_of_taxonomy ...')
   are not file-checked.

Usage:
    python3 scripts/check_manifest_integrity.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


_TASK_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    manifest_path = repo / "scripts" / "ingest_manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found", file=sys.stderr)
        return 1

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: manifest is not valid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(manifest, dict):
        print("ERROR: manifest root must be a JSON object", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_scripts: set[str] = set()
    runnable_count = 0

    for task_id, value in manifest.items():
        # Skip doc keys
        if task_id.startswith("_"):
            continue
        runnable_count += 1

        if not _TASK_ID_RE.match(task_id):
            errors.append(
                f"task '{task_id}': id must match {_TASK_ID_RE.pattern} "
                f"(lowercase, digits, underscores, starts with letter)"
            )

        if not isinstance(value, list) or not value:
            errors.append(
                f"task '{task_id}': value must be a non-empty list of shell commands"
            )
            continue

        for i, cmd in enumerate(value):
            if not isinstance(cmd, str) or not cmd.strip():
                errors.append(
                    f"task '{task_id}' command {i}: must be a non-empty string"
                )
                continue
            for tok in cmd.split():
                if tok.startswith("scripts/") and tok.endswith(".py"):
                    if not (repo / tok).exists():
                        errors.append(
                            f"task '{task_id}': script not found in repo: {tok}"
                        )
                    seen_scripts.add(tok)

    if errors:
        print(f"Manifest validation FAILED ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"Manifest OK: {runnable_count} task(s), "
        f"{len(seen_scripts)} unique script(s) referenced"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
