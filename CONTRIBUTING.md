# Contributing to WorldOfTaxonomy

---

## Rules

1. **TDD - Red, Green, Refactor.** Write the failing test first. Run it red. Then write the minimum implementation to make it green. Never skip the red step.
2. **No em-dashes.** Never use the em-dash character (U+2014) anywhere - code, comments, docstrings, markdown, or config. CI enforces this. Install the pre-commit hook to catch it locally: `pip install pre-commit && pre-commit install`.
3. **One system per PR.** Complete all steps (tests, ingester, CLI registration, docs update) in a single PR.

---

## Adding a Classification System

### Step 0 - Validate the data source

**Do not write any code until this step is complete.**

1. Download the data file to `data/`
2. Inspect the format: `head -20`, check delimiters, encoding, column names
3. Count actual records: `wc -l` (CSV) or `grep -c '<Element'` (XML)
4. Verify the license on the source website
5. Compute SHA-256: `sha256sum data/<file>`
6. If the count differs >20% from any prior estimate, stop and reassess
7. Record findings for the ingester docstring: verified count, format, license, hash

### Step 1 - Write RED tests

Create `tests/test_ingest_<system>.py` before any implementation.

Required test cases:

- **Parser count**: parsed nodes >= `_EXPECTED_MIN`
- **No duplicate codes**: `len(codes) == len(set(codes))`
- **Non-empty titles**: every node has a title
- **Parent validity**: every `parent_code` references an existing code
- **Level-1 roots**: level-1 nodes have `parent = None`
- **No em-dashes**: `"\u2014" not in title` for all nodes
- **Provenance in DB**: integration test asserts `data_provenance` and `source_file_hash` on the system row
- **Idempotency**: ingest twice, same count

For file-based systems, guard parser tests with:

```python
DATA_FILE = "data/<filename>"
HAS_DATA = os.path.exists(DATA_FILE)

@pytest.mark.skipif(not HAS_DATA, reason="data file not found")
class TestParser:
    ...
```

Canonical example: [test_ingest_icd10cm.py](tests/test_ingest_icd10cm.py)

Run it - every test must fail or error:

```bash
python3 -m pytest tests/test_ingest_<system>.py -v
```

### Step 2 - Write the ingester and run GREEN

Create `world_of_taxonomy/ingest/<system>.py`. Required elements:

- **Docstring**: source URL, data format, hierarchy description, overlap check vs existing systems, verified node count, SHA-256 hash
- **`_SYSTEM_ROW`**: tuple of `(id, name, full_name, version, region, authority)`
- **`_SOURCE_URL`**, **`_DATA_PROVENANCE`**, **`_LICENSE`**: provenance constants
- **`_EXPECTED_MIN`**: minimum node count (~80% of verified count). Ingestion raises `ValueError` if below this
- **`sha256_of_file()`**: import from `world_of_taxonomy.ingest.hash_util` and store the hash
- **`CHUNK = 500`**: batch insert size
- **Em-dash replacement**: `title.replace("\u2014", "-")` on every title

The system INSERT must include all provenance fields:

```python
await conn.execute(
    """INSERT INTO classification_system
           (id, name, full_name, version, region, authority,
            source_url, source_date, data_provenance, license,
            source_file_hash, node_count)
       VALUES ($1,$2,$3,$4,$5,$6,$7,CURRENT_DATE,$8,$9,$10,0)
       ON CONFLICT (id) DO UPDATE SET
            name=$2, full_name=$3, version=$4, region=$5, authority=$6,
            source_url=$7, source_date=CURRENT_DATE, data_provenance=$8,
            license=$9, source_file_hash=$10, node_count=0""",
    sid, short, full, ver, region, authority,
    _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, file_hash,
)
```

Canonical examples: [icd10cm.py](world_of_taxonomy/ingest/icd10cm.py) (file-based), [jsic.py](world_of_taxonomy/ingest/jsic.py) (embedded data)

Run tests green + em-dash check:

```bash
python3 -m pytest tests/test_ingest_<system>.py -v
python3 -c "import pathlib; [exit(1) for f in pathlib.Path('.').rglob('*.py') if b'\xe2\x80\x94' in f.read_bytes()]"
```

### Step 3 - Register in CLI and update docs

1. Add to `world_of_taxonomy/__main__.py` dispatch
2. Update `CLAUDE.md` - add row to systems table, update total node count
3. Update `DATA_SOURCES.md` - add attribution row
4. Update `CHANGELOG.md` - add entry under `[Unreleased]`

### Step 4 - Commit

```bash
git add world_of_taxonomy/ingest/<system>.py tests/test_ingest_<system>.py
git add world_of_taxonomy/__main__.py CLAUDE.md DATA_SOURCES.md CHANGELOG.md
git commit -m "feat: ingest <system> (<N> codes, TDD green)"
```

### Checklist

- [ ] Data file downloaded, inspected, counted, license verified, SHA-256 computed
- [ ] Tests written and confirmed red
- [ ] Ingester written with all provenance fields
- [ ] Tests pass green
- [ ] Em-dash check passes
- [ ] CLI registered
- [ ] CLAUDE.md, DATA_SOURCES.md, CHANGELOG.md updated
- [ ] Full test suite passes: `python3 -m pytest tests/ -v`

---

## Adding a Domain Deep-Dive Taxonomy

Follow Steps 0-4 above with these additions:

1. Register in **both** `classification_system` (FK requirement) and `domain_taxonomy`
2. After inserting nodes, update **both** `classification_system.node_count` and `domain_taxonomy.code_count`
3. Link parent industry nodes via `node_taxonomy_link` (not `equivalence`)

```python
await conn.executemany(
    """INSERT INTO node_taxonomy_link (system_id, node_code, taxonomy_id, relevance)
       VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING""",
    [("naics_2022", code, "domain_<type>", "primary") for code in naics_codes],
)
```

Code prefix convention: 3-letter prefix, e.g. `dtf_` (domain truck freight).

Canonical example: [domain_truck_freight.py](world_of_taxonomy/ingest/domain_truck_freight.py)

---

## Ingester Patterns

| Format | Example | Use when |
|--------|---------|----------|
| CSV/TSV from ZIP | [ndc_fda.py](world_of_taxonomy/ingest/ndc_fda.py) | Tab/comma-delimited in ZIP |
| Fixed-width text | [icd10cm.py](world_of_taxonomy/ingest/icd10cm.py) | CMS-style order files |
| XML | [mesh.py](world_of_taxonomy/ingest/mesh.py) | Structured XML |
| Pipe-delimited | [nci_thesaurus.py](world_of_taxonomy/ingest/nci_thesaurus.py) | NCI-style flat files |
| Embedded list | [jsic.py](world_of_taxonomy/ingest/jsic.py) | Small systems (<100 nodes) |
| Derived copy | [nace_derived.py](world_of_taxonomy/ingest/nace_derived.py) | National NACE/ISIC adoptions |

---

## Data Provenance

Every ingester must record 5 provenance fields on the `classification_system` row:

| Field | Description |
|-------|-------------|
| `source_url` | Where the data was downloaded from |
| `source_date` | When it was ingested (set to `CURRENT_DATE`) |
| `data_provenance` | One of the 4 tiers below |
| `license` | License string (e.g., "Public Domain (US Government)") |
| `source_file_hash` | SHA-256 of the data file (use `hash_util.sha256_of_file()`) |

### Provenance tiers

| Tier | Value | Meaning | Example |
|------|-------|---------|---------|
| 1 | `official_download` | Parsed from official source file with SHA-256 | ICD-10-CM (CMS) |
| 2 | `structural_derivation` | Copied from parent standard | WZ 2008 from NACE |
| 3 | `manual_transcription` | Transcribed from documentation | JSIC divisions |
| 4 | `expert_curated` | Domain expert-created | Domain taxonomies |

### Audit endpoints

| Surface | Endpoint |
|---------|----------|
| REST API | `GET /api/v1/audit/provenance` - tier breakdown, missing hashes, skeleton systems |
| MCP | Tool: `get_audit_report` - same data |
| Frontend | Provenance badge on system and node detail pages |

### Verification query

```sql
SELECT data_provenance, count(*) AS systems, sum(node_count) AS nodes
FROM classification_system
GROUP BY data_provenance
ORDER BY nodes DESC;
```

---

## Code Style

- No speculative code - implement only what a test requires
- Backend: Python type hints on all public functions
- Frontend: TypeScript strict mode, no `any`
- All async database functions use `asyncpg` connection parameter `conn`

---

## Running Tests

```bash
# Full suite
python3 -m pytest tests/ -v

# Single file
python3 -m pytest tests/test_ingest_naics.py -v
```

Tests use a `test_wot` PostgreSQL schema isolated from production. Never query the `public` schema in tests.

---

## Questions

Open an issue at https://github.com/colaberry/WorldOfTaxonomy/issues.
