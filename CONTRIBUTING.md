# Contributing to WorldOfTaxanomy

## How to Add a New Classification System

Every new classification system follows the same pattern. This guide walks through each step.

### Step 1 - Write RED tests first (TDD, mandatory)

Create `tests/test_ingest_<system>.py` before writing any implementation code.

```python
"""Tests for <system> ingester."""
import pytest
from world_of_taxanomy.ingest.<system> import (
    _determine_level,
    _determine_parent,
    _determine_sector,
    ingest_<system>,
)


class TestXxxDetermineLevel:
    def test_...(self):
        assert _determine_level("...") == 1

    # 4-6 test cases total


class TestXxxDetermineParent:
    def test_root_has_no_parent(self):
        assert _determine_parent("A") is None

    # 4-6 test cases total


class TestXxxDetermineSector:
    def test_...(self):
        assert _determine_sector("...") == "..."

    # 4-6 test cases total


def test_ingest_xxx_from_real_file(db_pool):
    pytest.skip("Download data/<file> first")
    # integration test body here
```

Run it - every test must FAIL (red). If any test passes, the test is trivially true and needs fixing.

Commit the failing tests:
```bash
git add tests/test_ingest_<system>.py
git commit -m "test: RED tests for <system> ingester"
```

### Step 2 - Write the ingester

Create `world_of_taxanomy/ingest/<system>.py`:

```python
"""<System name> ingester.

Source: <URL>
License: <License>
Download: <instructions if manual>
"""
from typing import Optional
from world_of_taxanomy.ingest.base import ensure_data_file


DATA_URL = "<url>"
DATA_PATH = "data/<filename>"


def _determine_level(code: str) -> int:
    """Return hierarchy depth: 1 = top-level sector, deeper = more specific."""
    ...


def _determine_parent(code: str) -> Optional[str]:
    """Return parent code, or None if this is a root node."""
    ...


def _determine_sector(code: str) -> str:
    """Return the top-level sector code for this node."""
    ...


async def ingest_<system>(conn, path=None) -> int:
    """Ingest <System> into the database. Returns number of nodes inserted."""
    path = path or DATA_PATH
    await ensure_data_file(DATA_URL, path)

    # 1. Upsert the system record
    await conn.execute(
        """INSERT INTO classification_system (id, name, version, region, node_count)
           VALUES ($1, $2, $3, $4, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "<system_id>", "<System Name>", "<version>", "<region>",
    )

    # 2. Parse the file into (code, title, level, parent, sector, seq) tuples
    nodes = []
    seq = 0
    # ... parsing logic ...

    # 3. Detect leaves
    parent_set = {n[3] for n in nodes if n[3] is not None}

    # 4. Batch insert nodes
    for code, title, level, parent, sector, seq in nodes:
        is_leaf = code not in parent_set
        await conn.execute(
            """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf, seq_order)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT DO NOTHING""",
            "<system_id>", code, title, level, parent, sector, is_leaf, seq,
        )

    # 5. Update node count
    count = len(nodes)
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, "<system_id>",
    )
    return count
```

### Step 3 - Run tests green

```bash
python3 -m pytest tests/test_ingest_<system>.py -v
```

All tests must pass. If any fail, fix the implementation - do NOT change the test to match a broken implementation.

Run the full suite to confirm nothing broke:
```bash
python3 -m pytest tests/ -v --tb=short
```

### Step 4 - Register in the CLI

Edit `world_of_taxanomy/__main__.py`:
1. Add `"<system_id>"` to the `choices` list in the `ingest` subcommand
2. Add an `elif args.system == "<system_id>":` branch in `cmd_ingest()` that calls `ingest_<system>`

### Step 5 - Update documentation

- `CLAUDE.md` - mark the system row as done with actual code count
- `data/README.md` - add source URL, license, file format
- `DATA_SOURCES.md` - add attribution row
- `CHANGELOG.md` - add entry under `[Unreleased]`
- `world_of_taxanomy/api/app.py` LLMS_TXT - add to the `## Systems` section

### Step 6 - Commit and send report

```bash
git add world_of_taxanomy/ingest/<system>.py tests/test_ingest_<system>.py
git add world_of_taxanomy/__main__.py CLAUDE.md CHANGELOG.md data/README.md DATA_SOURCES.md
git commit -m "feat: ingest <system> (<N> codes, TDD green)"
```

Verify the git log shows the RED commit before the GREEN commit:
```bash
git log --oneline -5
```

---

## Code Style

- No em-dashes (`-`) anywhere - use a hyphen `-` instead
- No speculative code - implement only what a test requires
- All strings in Python are plain ASCII unless the source data requires Unicode
- Backend: Python type hints on all public functions
- Frontend: TypeScript strict mode, no `any`

## Development Practices

- TDD is mandatory. Red -> Green -> Refactor. Never skip the red step.
- One system per session. Complete all steps before moving to the next.
- The `test_wot` PostgreSQL schema is used for all tests. Never query `public` in tests.

## Running Tests

```bash
# Full suite
python3 -m pytest tests/ -v

# Single file
python3 -m pytest tests/test_ingest_naics.py -v

# With coverage
python3 -m pytest tests/ --cov=world_of_taxanomy
```

## Questions

Open an issue on GitHub.
