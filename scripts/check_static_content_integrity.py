#!/usr/bin/env python3
"""Validate frontend/public/llms-codes/ against its .manifest.json.

This runs in CI without a database. It catches structural drift:
manifest references a file that doesn't exist, or a file exists that
the manifest doesn't know about. It does NOT detect content drift from
the live DB - that's the pre-push hook's job.

Exit 0 if clean, 1 if any inconsistency found.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DIR = PROJECT_ROOT / "frontend" / "public" / "llms-codes"
MANIFEST = DIR / ".manifest.json"
INDEX = DIR / "index.txt"


def main() -> int:
    if not DIR.exists():
        print("[check-static] llms-codes/ does not exist yet; skipping (pre-bootstrap).")
        return 0

    if not MANIFEST.exists():
        print(f"[check-static] missing manifest: {MANIFEST}", file=sys.stderr)
        return 1

    if not INDEX.exists():
        print(f"[check-static] missing index: {INDEX}", file=sys.stderr)
        return 1

    try:
        manifest = json.loads(MANIFEST.read_text())
    except Exception as exc:
        print(f"[check-static] manifest is not valid JSON: {exc}", file=sys.stderr)
        return 1

    expected: set[Path] = {MANIFEST, INDEX}
    errors: list[str] = []

    for system_id, entry in manifest.items():
        files = entry.get("files") or []
        if not files:
            errors.append(f"{system_id}: manifest entry has no files")
            continue
        for rel in files:
            p = DIR / rel
            expected.add(p)
            if not p.exists():
                errors.append(f"{system_id}: file in manifest does not exist: {rel}")
            elif p.stat().st_size == 0:
                errors.append(f"{system_id}: file is empty: {rel}")

    actual: set[Path] = set()
    for p in DIR.rglob("*"):
        if p.is_file():
            actual.add(p)

    orphans = sorted(actual - expected)
    if orphans:
        for p in orphans:
            errors.append(f"orphan file (not in manifest): {p.relative_to(DIR)}")

    if errors:
        print("[check-static] FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"[check-static] ok: {len(manifest)} systems, "
        f"{len(expected) - 2} files, manifest + index present"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
