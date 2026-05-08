"""Auto-ingest classification systems whose ingester module was just added.

Closes the gap that let PRs merge ingester code without ever loading
data into prod (root cause of the 2026-05 "1,000 vs 1,005 systems"
incident).

How it fits in
--------------
- Triggered by ``.github/workflows/auto-ingest-on-merge.yml`` on every
  push to main that touches ``world_of_taxonomy/ingest/**.py``.
- The workflow runs ``git diff --name-status HEAD^ HEAD`` to find files
  ADDED (not modified) under ``world_of_taxonomy/ingest/`` and passes
  them to this script via ``ADDED_FILES`` env (space-separated paths).
- For each added file we map ``module name -> CLI target`` by regexing
  the dispatcher in ``world_of_taxonomy/__main__.py``, then run
  ``python -m world_of_taxonomy ingest <target>`` against
  ``DATABASE_URL`` for each unique target.
- Modified ingesters are intentionally NOT re-run: scheduled refresh
  handles upstream-corrections, and we don't want every doc-fix typo
  push to re-shuffle the entire dataset.

Why regex instead of import
---------------------------
Importing ``world_of_taxonomy.__main__`` evaluates the argparse setup
and the heavy ingest module imports lazily-but-eagerly. We want to run
on a clean CI image with the full ``requirements.txt`` deps installed
but without paying the full import cost just to read a string list.

The dispatcher pattern is stable and enforced by the PR template:

    if target in ("<target>", "all"):
        from world_of_taxonomy.ingest.<module> import <fn>

If a contributor breaks this pattern (e.g., uses a non-standard
match), this script will skip the affected module and emit a WARN.
The auto-load won't fire, but the existing manual ``workflow_dispatch``
on ``ingest-refresh.yml`` remains as a fallback.

Crosswalks
----------
Crosswalk targets (``crosswalk_*``) frequently depend on multiple
anchor systems being loaded first. Auto-loading them on every push
would race with whatever order the PRs merged in. We deliberately
skip them; they ship via the monthly cron in ``ingest-refresh.yml``
or via manual ``workflow_dispatch``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = REPO_ROOT / "world_of_taxonomy" / "__main__.py"

# Match every ingest dispatch block in __main__.py. The pattern is:
#     if target in ("<target>", "all"):
#         from world_of_taxonomy.ingest.<module> import <fn>
# Anchored to the "all" arm so we don't catch unrelated tuples elsewhere.
DISPATCH_RE = re.compile(
    r'if\s+target\s+in\s+\(\s*"([\w]+)"\s*,\s*"all"\s*\):\s*\n'
    r"\s*from\s+world_of_taxonomy\.ingest\.(\w+)\s+import",
)

# Targets we never auto-load on merge, even if the dispatcher names them.
# Crosswalks need anchors loaded first; "all" is an umbrella.
SKIP_PREFIXES = ("crosswalk_", "crosswalk")
SKIP_EXACT = {"all"}


def build_module_to_targets() -> dict[str, list[str]]:
    """Return ``{ingest_module: [cli_target, ...]}`` from the dispatcher.

    Most ingesters back exactly one target. A few (e.g. ``nace_derived``
    powers ``wz`` / ``onace`` / ``noga``) back several; we keep all of
    them so the workflow can ingest each.
    """
    src = MAIN_PY.read_text()
    out: dict[str, list[str]] = {}
    for target, module in DISPATCH_RE.findall(src):
        if target in SKIP_EXACT:
            continue
        if any(target.startswith(p) for p in SKIP_PREFIXES):
            continue
        out.setdefault(module, []).append(target)
    return out


def parse_added_files(raw: str) -> list[str]:
    """Split a whitespace-separated list of file paths."""
    if not raw:
        return []
    return [p.strip() for p in raw.split() if p.strip()]


def filter_ingest_files(paths: list[str]) -> list[str]:
    """Keep only added ``.py`` files under ``world_of_taxonomy/ingest/``.

    Excludes private modules (``_`` prefix) and the shared ``base.py``,
    which never have a CLI target of their own.
    """
    keep: list[str] = []
    for p in paths:
        if not p.startswith("world_of_taxonomy/ingest/"):
            continue
        if not p.endswith(".py"):
            continue
        name = Path(p).name
        if name.startswith("_") or name == "base.py":
            continue
        keep.append(p)
    return keep


def main() -> int:
    added = parse_added_files(os.environ.get("ADDED_FILES", ""))
    if not added and len(sys.argv) > 1:
        added = list(sys.argv[1:])

    ingest_files = filter_ingest_files(added)
    if not ingest_files:
        print("No new ingester modules in this push; nothing to do.")
        return 0

    mod_to_targets = build_module_to_targets()

    targets: list[str] = []
    skipped_modules: list[str] = []
    for path in ingest_files:
        module = Path(path).stem
        mapped = mod_to_targets.get(module, [])
        if mapped:
            targets.extend(mapped)
        else:
            skipped_modules.append(module)

    if skipped_modules:
        print(
            "WARN: ingester module(s) not wired into __main__.py "
            f"dispatcher: {skipped_modules}. Skipping. The PR template's "
            "'New classification system' checklist should have flagged "
            "this; please verify.",
            file=sys.stderr,
        )

    # De-dupe while preserving order.
    seen: set[str] = set()
    unique_targets = [t for t in targets if not (t in seen or seen.add(t))]
    if not unique_targets:
        print("No mapped CLI targets to ingest.")
        return 0

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set; refusing to dispatch.", file=sys.stderr)
        return 2

    print(f"Auto-ingesting {len(unique_targets)} system(s): {unique_targets}")

    failures: list[str] = []
    for target in unique_targets:
        print(f"\n=== ingest {target} ===", flush=True)
        rc = subprocess.call(
            [sys.executable, "-m", "world_of_taxonomy", "ingest", target],
            cwd=str(REPO_ROOT),
        )
        if rc != 0:
            print(f"FAIL: target={target} rc={rc}", flush=True)
            failures.append(target)

    if failures:
        print(
            f"\n{len(failures)} ingester(s) failed: {failures}.\n"
            "Re-run via: gh workflow run ingest-refresh.yml "
            "-f target=<failed_target> --repo colaberry/WorldOfTaxonomy",
            file=sys.stderr,
        )
        return 1

    print(f"\nIngested {len(unique_targets)} new system(s) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
