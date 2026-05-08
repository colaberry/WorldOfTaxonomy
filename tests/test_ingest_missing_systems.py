"""Unit tests for scripts/ingest_missing_systems.py.

The module is the "engine room" for the Auto ingest on merge workflow:
it parses world_of_taxonomy/__main__.py to map newly-added ingester
modules to their CLI targets. If the regex drifts or the dispatcher
pattern changes, brand-new systems would silently fail to load on
prod (which is the original incident this fix addresses).

These tests pin the contract: regardless of how big the dispatcher
grows, the parser must keep extracting at least the well-known
target -> module pairs that exist today, must skip crosswalk_*
targets, and must handle the edge cases (private modules, base.py,
non-ingest paths) the workflow throws at it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "ingest_missing_systems.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "ingest_missing_systems", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_file_exists():
    assert SCRIPT_PATH.exists(), f"missing {SCRIPT_PATH}"


def test_dispatch_regex_extracts_known_systems():
    """Mapping must include every system whose absence broke prod in
    the original incident. If __main__.py's dispatcher pattern drifts
    so any of these stop being discoverable, the auto-ingest workflow
    will silently no-op on the next new system."""
    mod = _load_module()
    mapping = mod.build_module_to_targets()

    expected = {
        "naics": "naics",
        "isic": "isic",
        "fibo": "fibo",
        "wordnet_nouns": "wordnet_nouns",
        "gs1_gpc": "gs1_gpc",
        "geonames_features": "geonames_features",
        # Known mismatch: module name 'schemaorg' but target 'schema_org'
        "schemaorg": "schema_org",
    }
    for module_name, expected_target in expected.items():
        assert module_name in mapping, (
            f"module '{module_name}' not found in dispatcher map; "
            f"present modules: {sorted(mapping)[:10]}..."
        )
        assert expected_target in mapping[module_name], (
            f"module '{module_name}' should map to target "
            f"'{expected_target}' but maps to {mapping[module_name]}"
        )


def test_dispatcher_skips_crosswalk_and_all():
    """Crosswalks need anchors loaded first; auto-ingest skips them."""
    mod = _load_module()
    mapping = mod.build_module_to_targets()
    flat_targets = {t for ts in mapping.values() for t in ts}
    assert "all" not in flat_targets
    crosswalk_targets = [t for t in flat_targets if t.startswith("crosswalk")]
    assert crosswalk_targets == [], (
        f"crosswalk_* targets must be skipped by the auto-ingest mapping "
        f"but got: {crosswalk_targets[:5]}"
    )


def test_filter_ingest_files_strips_non_ingest_paths():
    mod = _load_module()
    paths = [
        "world_of_taxonomy/ingest/fibo.py",
        "world_of_taxonomy/ingest/_internal.py",
        "world_of_taxonomy/ingest/base.py",
        "world_of_taxonomy/api/routers/billing.py",
        "tests/test_ingest_fibo.py",
        "world_of_taxonomy/ingest/gs1_gpc.py",
        "scripts/build_llms_txt.py",
    ]
    kept = mod.filter_ingest_files(paths)
    assert kept == [
        "world_of_taxonomy/ingest/fibo.py",
        "world_of_taxonomy/ingest/gs1_gpc.py",
    ]


def test_parse_added_files_handles_whitespace():
    mod = _load_module()
    assert mod.parse_added_files("") == []
    assert mod.parse_added_files("   ") == []
    assert mod.parse_added_files("a.py b.py") == ["a.py", "b.py"]
    assert mod.parse_added_files("  a.py\nb.py  c.py ") == ["a.py", "b.py", "c.py"]


def test_main_no_op_when_no_added_files(monkeypatch, capsys):
    mod = _load_module()
    monkeypatch.delenv("ADDED_FILES", raising=False)
    monkeypatch.setattr(mod.sys, "argv", ["ingest_missing_systems.py"])
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "nothing to do" in out.lower()


def test_main_no_op_when_only_non_ingest_paths(monkeypatch, capsys):
    mod = _load_module()
    monkeypatch.setenv(
        "ADDED_FILES",
        "tests/test_x.py world_of_taxonomy/api/foo.py docs/runbook.md",
    )
    monkeypatch.setattr(mod.sys, "argv", ["ingest_missing_systems.py"])
    rc = mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "nothing to do" in out.lower()


def test_main_refuses_without_database_url(monkeypatch, capsys):
    """If the workflow forgets to pass DATABASE_URL, we exit 2 rather
    than silently doing nothing. Catches a misconfigured workflow."""
    mod = _load_module()
    monkeypatch.setenv(
        "ADDED_FILES", "world_of_taxonomy/ingest/fibo.py"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    rc = mod.main()
    assert rc == 2
    err = capsys.readouterr().err
    assert "DATABASE_URL" in err
