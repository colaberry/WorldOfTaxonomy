# SOP: Adding a New Classification System

This document is the definitive guide for adding a new classification system
to WorldOfTaxonomy. Follow every step in order. Do not skip the TDD cycle.

---

## 1. Before You Start

**Prerequisites**

- Local dev DB running (`postgresql://wot:wotpass@localhost:5432/worldoftaxonomy`)
- `.env` file present with `DATABASE_URL` set
- Existing tests passing: `python3 -m pytest tests/ -q`

**Decide the system ID**

The system ID is a short, lowercase, underscore-separated string used as the
primary key in `classification_system`. It must be unique across the entire
graph. Examples: `isic_rev4`, `nace_rev2`, `ford_frascati`, `ciiu_pe`.

Rules:
- Lowercase, no hyphens (use underscores)
- No spaces
- Prefer official acronym + version: `atc_who`, `hs2022`, `icd10_gm`
- Country suffixes for national variants: `isic_ng`, `ciiu_co`

---

## 2. Classify the System Type

Choose one of three implementation paths:

| Type | When to use | Implementation location |
|------|-------------|------------------------|
| **Derived from NACE Rev 2** | National adaptation of NACE (EU countries, Turkey) | Add `_SystemMeta` + wrapper function to `world_of_taxonomy/ingest/nace_derived.py` |
| **Derived from ISIC Rev 4** | National adaptation of ISIC Rev 4 (LATAM, Asia, Africa, Middle East) | Add `_SystemMeta` + wrapper function to `world_of_taxonomy/ingest/isic_derived.py` |
| **Standalone** | Any system not directly derived from NACE or ISIC | Create `world_of_taxonomy/ingest/{system_id}.py` |

**How to tell if a system is derived**

A system is NACE-derived if its national statistical office explicitly states
codes are aligned 1:1 with NACE Rev 2 at the 4-digit class level (e.g., all
EU NACE national adaptations). It is ISIC-derived if it follows the same
structure as ISIC Rev 4 at the 4-digit class level (e.g., CIIU countries in
Latin America, VSIC in Vietnam).

If there are country-specific extensions or renumbered codes, start with the
derived path anyway and note that extensions can be added later.

---

## 3. TDD Cycle (Red - Green - Refactor)

**The test must be written and confirmed failing BEFORE the implementation.**
This is not optional.

### Step 3a: Write the test file

Create `tests/test_ingest_{system_id}.py`:

```python
"""Tests for {Full Name} ({system_id}) ingester."""

import asyncio
import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get_system(conn, system_id: str):
    return await conn.fetchrow(
        "SELECT * FROM classification_system WHERE id = $1", system_id
    )


async def _count_nodes(conn, system_id: str) -> int:
    row = await conn.fetchrow(
        "SELECT count(*) AS cnt FROM classification_node WHERE system_id = $1",
        system_id,
    )
    return row["cnt"]


class TestIngest{SystemId}:  # CamelCase of system_id

    def test_ingest_creates_system(self, db_pool):
        from world_of_taxonomy.ingest.{system_id} import ingest_{system_id}

        async def _test():
            async with db_pool.acquire() as conn:
                count = await ingest_{system_id}(conn)
                assert count >= {min_expected_nodes}

                sys = await _get_system(conn, "{system_id}")
                assert sys is not None
                assert sys["name"] == "{Expected Name}"
                assert sys["node_count"] == count

        _run(_test())

    def test_ingest_creates_nodes(self, db_pool):
        from world_of_taxonomy.ingest.{system_id} import ingest_{system_id}

        async def _test():
            async with db_pool.acquire() as conn:
                count = await ingest_{system_id}(conn)
                db_count = await _count_nodes(conn, "{system_id}")
                assert db_count == count

        _run(_test())

    def test_idempotent(self, db_pool):
        from world_of_taxonomy.ingest.{system_id} import ingest_{system_id}

        async def _test():
            async with db_pool.acquire() as conn:
                count1 = await ingest_{system_id}(conn)
                count2 = await ingest_{system_id}(conn)
                db_count = await _count_nodes(conn, "{system_id}")
                assert db_count == count1  # second run does not duplicate

        _run(_test())
```

For **ISIC-derived systems**, the node count equals however many `isic_rev4`
nodes are in the test DB. Query it dynamically instead of hardcoding:

```python
    def test_ingest_creates_system(self, db_pool):
        from world_of_taxonomy.ingest.isic_derived import ingest_{system_id}

        async def _test():
            async with db_pool.acquire() as conn:
                isic_count = await _count_nodes(conn, "isic_rev4")
                count = await ingest_{system_id}(conn)
                assert count == isic_count
                sys = await _get_system(conn, "{system_id}")
                assert sys["region"] == "{Country Name}"

        _run(_test())
```

Apply the same pattern for NACE-derived systems (query `nace_rev2` count).

### Step 3b: Confirm the test fails (Red)

```bash
python3 -m pytest tests/test_ingest_{system_id}.py -v
```

Expected output: `ImportError` or `ModuleNotFoundError`. If the test passes
without an implementation, something is wrong - check for a naming collision
with an existing module.

---

## 4. Write the Ingester

### Path A: NACE-derived

Open `world_of_taxonomy/ingest/nace_derived.py` and add:

1. A `_SystemMeta` NamedTuple instance:

```python
_MY_SYSTEM = _SystemMeta(
    id="my_system",
    name="Short Display Name",
    full_name="Full Official Name in the Official Language",
    region="Country Name",
    version="Rev X",
    authority="Official Authority Name (abbreviation)",
    tint_color="#XXXXXX",  # hex color, pick something distinct
)
```

2. A public wrapper function at the bottom of the file:

```python
async def ingest_my_system(conn) -> int:
    """Ingest [Country] [System Name].

    Derives all codes from NACE Rev 2 already present in the database.
    National extensions can be added later from [authority] data files.
    """
    return await _ingest_derived_from_nace(conn, _MY_SYSTEM)
```

### Path B: ISIC-derived

Same as Path A but in `world_of_taxonomy/ingest/isic_derived.py`, using
`_ingest_derived_from_isic(conn, meta)`.

### Path C: Standalone

Create `world_of_taxonomy/ingest/{system_id}.py`:

```python
"""[Full System Name] ingester.

[Two to four sentences explaining: what this system classifies, who uses it,
and why it is not already covered by existing systems in the graph.]
"""
from __future__ import annotations

SYSTEM_ID = "{system_id}"

# Provenance metadata. See Appendix F for what to put here.
_SOURCE_URL = "https://authority.example/data.xlsx"
_DATA_PROVENANCE = "official_download"  # or manual_transcription / structural_derivation / expert_curated
_LICENSE = "Public Domain"
# Per-code authority deep link. `{code}` is interpolated on response.
# Use None when the authority has no per-code page.
_NODE_URL_TEMPLATE = "https://authority.example/code/{code}"

# (code, title, level, parent_code)
# parent_code = None for root nodes
NODES: list[tuple] = [
    # Roots
    ("A",   "Section A Title",   1, None),
    ("B",   "Section B Title",   1, None),
    # Children
    ("A1",  "Group A1 Title",    2, "A"),
    ("A2",  "Group A2 Title",    2, "A"),
]


async def ingest_{system_id}(conn) -> int:
    """Ingest [Full System Name]."""
    await conn.execute(
        """
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, tint_color,
             source_url, source_date, data_provenance, license, node_url_template)
        VALUES ($1, $2, $3, $4, $5, $6, $7,
                $8, CURRENT_DATE, $9, $10, $11)
        ON CONFLICT (id) DO UPDATE SET
            node_count = 0,
            source_url = EXCLUDED.source_url,
            source_date = CURRENT_DATE,
            data_provenance = EXCLUDED.data_provenance,
            license = EXCLUDED.license,
            node_url_template = EXCLUDED.node_url_template
        """,
        SYSTEM_ID,
        "Display Name",
        "Full Official Name",
        "Region / Country",
        "Version or Year",
        "Issuing Authority",
        "#XXXXXX",
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, _NODE_URL_TEMPLATE,
    )

    # Compute leaf flags dynamically - never assume a fixed depth
    codes_with_children = {parent for (_, _, _, parent) in NODES if parent is not None}

    count = 0
    for seq, (code, title, level, parent_code) in enumerate(NODES, 1):
        sector = code[:2]   # adjust as appropriate for this system
        is_leaf = code not in codes_with_children
        await conn.execute(
            """
            INSERT INTO classification_node
                (system_id, code, title, level, parent_code,
                 sector_code, is_leaf, seq_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (system_id, code) DO NOTHING
            """,
            SYSTEM_ID, code, title, level, parent_code, sector, is_leaf, seq,
        )
        count += 1

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, SYSTEM_ID,
    )
    print(f"  Ingested {count} {SYSTEM_ID} codes")
    return count
```

**NODES list rules:**
- Each entry is `(code, title, level, parent_code)`
- `code` must be unique within the system
- `level` is an integer; use 1 for roots, 2 for leaves (add more levels for
  deep hierarchies, adjusting `is_leaf` logic accordingly)
- `parent_code` is `None` for roots; must reference a code at `level - 1`
- Codes must not duplicate across levels (e.g., if "A" is both a level-1 root
  and a level-2 leaf, one insert will silently be dropped by `ON CONFLICT DO NOTHING`)

---

## 5. Confirm Tests Pass (Green)

```bash
python3 -m pytest tests/test_ingest_{system_id}.py -v
```

All three tests must pass. If `test_ingest_creates_nodes` fails with a count
mismatch, check for duplicate codes in the NODES list.

---

## 6. Wire into `__main__.py`

Two changes are required in `world_of_taxonomy/__main__.py`:

**6a. Add a dispatch block** - insert this block inside `async def _ingest()`,
grouped logically near similar systems:

```python
            if target in ("{system_id}", "all"):
                from world_of_taxonomy.ingest.{module} import ingest_{system_id}
                print("\n-- {Description} --")
                n = await ingest_{system_id}(conn)
                print(f"  {n} nodes")
```

- For derived systems, `{module}` is `nace_derived` or `isic_derived`
- For standalone systems, `{module}` is `{system_id}`

**6b. Add to the choices list** - find the `choices=[...]` argument of the
`ingest` subcommand parser and insert the new system ID before `"all"`:

```python
        choices=[..., "existing_last_id", "{system_id}", "all"],
```

**Verify syntax:**

```bash
python3 -c "import ast; ast.parse(open('world_of_taxonomy/__main__.py').read()); print('OK')"
```

---

## 7. Ingest to Dev DB

```bash
source .env
python3 -m world_of_taxonomy ingest {system_id}
```

Expected output: `Ingested N {system_id} codes` followed by `Ingestion complete.`

Spot-check via the REST API (requires the server running):

```bash
curl "http://localhost:8000/api/v1/systems/{system_id}"
curl "http://localhost:8000/api/v1/systems/{system_id}/nodes?limit=5"
```

---

## 8. Update CLAUDE.md

Two changes:

**8a. Update the header counts** at the top of CLAUDE.md:

```
WorldOfTaxonomy is a unified global industry classification knowledge graph.
It connects N classification systems ...

**N systems, X nodes, Y crosswalk edges.**
```

Get the current live counts:

```bash
source .env
python3 -c "
import asyncio, asyncpg, os
async def stats():
    c = await asyncpg.connect(os.environ['DATABASE_URL'], statement_cache_size=0)
    s = await c.fetchrow('SELECT count(*) FROM classification_system')
    n = await c.fetchrow('SELECT sum(node_count) FROM classification_system')
    e = await c.fetchrow('SELECT count(*) FROM equivalence')
    print(f'Systems: {s[0]}  Nodes: {n[0]}  Edges: {e[0]}')
    await c.close()
asyncio.run(stats())
"
```

**8b. Append a table row** to the systems table:

```markdown
| Display Name | Region | Node Count |
```

---

## 9. Run Full Test Suite

```bash
python3 -m pytest tests/ -q
```

All tests must pass before committing. A single failure anywhere blocks the commit.

---

## 10. Commit

Stage only the files you changed:

```bash
git add world_of_taxonomy/ingest/{system_id}.py   # standalone only
git add world_of_taxonomy/ingest/nace_derived.py  # if NACE-derived
git add world_of_taxonomy/ingest/isic_derived.py  # if ISIC-derived
git add tests/test_ingest_{system_id}.py
git add world_of_taxonomy/__main__.py
git add CLAUDE.md
```

Commit message format:

```
feat: ingest {Full System Name} ({system_id}, N nodes)
```

---

## Appendix A: Choosing a `tint_color`

The `tint_color` hex value is used by the frontend for visual identification.
Pick a color that is visually distinct from neighboring systems in the same
geographic region or classification family. Avoid exact duplicates within any
regional cluster.

Common palette guidance:
- EU/Europe: blues, teals, purples
- Latin America: yellows, ambers, greens
- Asia-Pacific: reds, pinks, sky blues
- Africa/Middle East: oranges, deep greens, indigos
- Global/UN: slates, grays, cyans

---

## Appendix B: Equivalence Edges

The derived-system ingesters automatically create bidirectional `exact` match
equivalence edges in the `equivalence` table. For standalone systems, add
equivalences manually if the system maps to another system already in the graph:

```python
# Forward: new_system -> target_system
await conn.execute(
    """
    INSERT INTO equivalence
        (source_system, source_code, target_system, target_code, match_type)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (source_system, source_code, target_system, target_code)
    DO NOTHING
    """,
    new_system_id, new_code, target_system_id, target_code, "exact",
)
```

Match types in use: `exact`, `broader`, `narrower`, `related`.

---

## Appendix C: Multi-Level Hierarchies

For systems deeper than 2 levels, adjust the ingester to handle 3 or more
levels. The key change is the `is_leaf` flag - only the deepest nodes should
have `is_leaf = True`:

```python
# 4-level example (section, division, group, class)
is_leaf = (level == 4)
```

The `sector_code` field should always point to the level-1 ancestor code.
For deep hierarchies, derive it from the code prefix or pass it explicitly
in the NODES tuple.

---

## Appendix D: Frontend Route Gating Rules

The `/codes` hub lists every system in the database, grouped by region. Each card deep-links to `/codes/[system]` and `/codes/[system]/[code]` via ISR. New systems must be reachable through these routes without a code change to the frontend.

### The rule

`MAJOR_SYSTEMS` in `frontend/src/app/codes/constants.ts` is a **build-time SSG scope list**, not a runtime allowlist.

Uses of `MAJOR_SYSTEMS` that are correct:

| File | Use |
|------|-----|
| `frontend/src/app/codes/[system]/page.tsx` | `generateStaticParams()` returns `MAJOR_SYSTEMS` to pre-render only curated system hubs |
| `frontend/src/app/codes/[system]/[code]/page.tsx` | `generateStaticParams()` walks `MAJOR_SYSTEMS` x level-1 sectors |
| `frontend/src/app/sitemap.ts` | Sitemap deep-node URLs are emitted only for `MAJOR_SYSTEMS` to stay under Google's per-file limits |
| `frontend/src/app/crosswalks/[systemA]/to/[systemB]/page.tsx` | Only major-to-major pairs are pre-rendered and served |

Uses that would be WRONG and have caused site-wide 404s in the past:

```tsx
// ❌ Do NOT add this to /codes/[system]/page.tsx or /codes/[system]/[code]/page.tsx
if (!isMajorSystem(system)) {
  notFound()
}
```

That gate 404s the ~990 non-curated systems that the `/codes` hub now lists. The route's existing `try/catch -> notFound()` around `serverGetNode` / `serverGetSystem` already returns 404 for truly invalid system or code values - the backend is the source of truth for what exists.

### Why the rule exists

Historical context: when the `/codes` hub only listed the 10 `MAJOR_SYSTEMS`, hard-gating the dynamic route felt tidy. After the hub expanded to a global region-grouped directory, every non-major system started 404ing (e.g. `/codes/onet_soc/11-3021.00`, `/codes/domain_truck_freight/dtf_cargo`). The fix was to remove the gate, not to restrict the hub.

### Smoke test after every ingest

Run the backend and frontend dev servers, then:

```bash
SYSTEM=<new_system_id>
SAMPLE_CODE=<a top-level code you just ingested>
for url in \
  http://localhost:3001/codes/$SYSTEM \
  http://localhost:3001/codes/$SYSTEM/$SAMPLE_CODE; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' "$url") $url"
done
```

Both must return 200. If either 404s, the route was gated somewhere - fix the route, not the data.

### When to add to `MAJOR_SYSTEMS`

Add a system to `MAJOR_SYSTEMS` only if you want:

1. Its sector pages pre-rendered at build time (faster first paint, better for crawlers that don't wait for ISR)
2. Its sector URLs in the sitemap (SEO priority)
3. Its crosswalks to other major systems rendered at `/crosswalks/{id}/to/{other}`

Most newly ingested systems (national derivatives, domain taxonomies, long-tail additions) do not need this. ISR serves them fine on first request.

---

## Appendix E: Provenance fields

Every `classification_system` row carries provenance metadata so an auditor
can answer "where did this data come from, when, under what license" without
leaving the page, and so the node detail page can link every code back to
its authority.

| Column | What goes here |
|--------|----------------|
| `source_url` | URL of the file or page the ingester parsed. Use the most specific URL available (the XLSX itself, not a landing page) so the hash in `source_file_hash` is attributable. |
| `source_date` | Typically `CURRENT_DATE`. Captures when the row was last refreshed. |
| `data_provenance` | One of `official_download`, `manual_transcription`, `structural_derivation`, `expert_curated`. |
| `license` | The upstream license (`Public Domain`, `CC BY 4.0`, `OGL v3`, `proprietary`, ...). |
| `source_file_hash` | SHA-256 of the downloaded file (set by `ensure_data_file` for `official_download` systems). |
| `node_url_template` | Per-code URL template with a literal `{code}` placeholder. The API interpolates this into `NodeResponse.source_url_for_code` for every node response. Set to `NULL` when the authority has no per-code page. |

### Picking `node_url_template`

Test one code on the authority's site before committing. The template is a
straight string replacement: whatever goes in `classification_node.code` is
substituted into `{code}` verbatim, with no URL-encoding. If the authority
requires a different form of the code (lowercased, dot-inserted, hyphen
removed), translate it in the ingester before storing, not in the template.

Examples in the repo today:

- `naics_2022`: `https://www.census.gov/naics/?input={code}&year=2022` ([ingest/naics.py](../world_of_taxonomy/ingest/naics.py)) - the NAICS ingester is the reference implementation for `ON CONFLICT ... DO UPDATE SET node_url_template = EXCLUDED.node_url_template`.
- `naics_2017`, `naics_2012`: `NULL` (skeleton systems with synthetic codes)

### Changing the template for a deployed system

Re-running the ingester refreshes the column via `ON CONFLICT ... DO UPDATE`.
For prod deployments that cannot be re-ingested immediately, write an
Alembic migration with a targeted `UPDATE` (see [migrations/versions/0002_node_url_template.py](../migrations/versions/0002_node_url_template.py)
for the canonical pattern). Do not hand-edit prod via psql; leave an audit
trail.

---

## Appendix F: Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `count returned N but db has N-1` | Duplicate code in NODES | Find and deduplicate the repeated code |
| `ImportError` after wiring | Module name mismatch in dispatch block | Check `{module}` matches the actual filename |
| `test_idempotent fails` | Missing `ON CONFLICT ... DO NOTHING` | Add the conflict clause to all INSERT statements |
| `WARNING: No nace_rev2 nodes found` | NACE not yet ingested in test DB | Run `python3 -m world_of_taxonomy ingest nace` first |
| Test sees wrong node count for derived system | Test hardcodes expected count | Query the base system count dynamically in the test |
