# Contributing to WorldOfTaxonomy

---

## Rules

1. **TDD - Red, Green, Refactor.** Write the failing test first. Run it red. Then write the minimum implementation to make it green. Never skip the red step.
2. **No em-dashes.** Never use the em-dash character (U+2014) anywhere - code, comments, docstrings, markdown, or config. CI enforces this. Install the pre-commit hook to catch it locally: `pip install pre-commit && pre-commit install`.
3. **One system per PR.** Complete all steps (tests, ingester, CLI registration, docs update) in a single PR.

---

## Adding a Classification System

Before writing any code, confirm the proposed system fits the project's scope. The [Inclusion Policy](wiki/inclusion-policy.md) is the canonical answer to "should this be in WoT?": published external source, stable identifiers, enumerated or hierarchical structure, practical size. If the system fails any of those tests, surface it in an issue first to discuss before opening a PR.

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

### Step 4 - Enrich descriptions

After the ingester runs, the system has codes and titles in the DB but most rows have an empty `description`. Pick the right enrichment strategy by system size and source:

**Source has descriptions** (e.g., GeoNames feature codes, WordNet glosses, schema.org `rdfs:comment`). Use them as-is. Map the source's description column to `classification_node.description` directly in the ingester. No LLM needed.

**Small system** (under ~10K nodes without descriptions): use native Claude Code enrichment in a dev session.

```bash
python scripts/native_enrich.py --system <system_id> --batch-size 500
```

The script reads pending rows from the DB, prints a prompt for an interactive Claude Code session, reads the JSONL response, and applies UPSERTs. Faster and higher quality than the cloud pipeline for vocabularies that are well-represented in modern LLMs (schema.org, FIBO, GS1 GPC). One-shot for the seed; not automated.

**Large system** (10K+ nodes without descriptions): use the Track 2 verified-LLM pipeline.

```bash
nohup bash -c 'set -a; source .env; set +a; export PYTHONPATH=.; \
  STALL_SEC=1800 CHECK_SEC=300 SYSTEM=<system_id> CONCURRENCY=12 \
  bash scripts/track2_watchdog.sh' > /tmp/<system>_watchdog.log 2>&1 &
```

For the residue (no/uncertain verdicts), launch a second pass against the local qwen2.5:72b model:

```bash
OLLAMA_API_KEY=ollama OLLAMA_BASE_URL=http://localhost:11434/v1 \
  OLLAMA_MODEL=qwen2.5:72b VERIFIER_MODEL=qwen2.5:72b \
  python -u -m scripts.qwen_rescue --systems <system_id> --concurrency 1 --flush-every 100
```

Verify coverage before moving on:

```sql
SELECT count(*) total, count(description) with_desc,
       round(100.0 * count(description) / count(*), 2) AS pct
FROM classification_node WHERE system_id = '<system_id>';
```

Aim for >= 99% coverage on systems where descriptions are first-class. Lower targets (~95%) are acceptable when the LLM legitimately cannot generate a useful description for ambiguous codes.

### Step 5 - Update the wiki (Karpathy LLM Wiki Pattern)

WoT distributes editorial content through four channels: web `/guide/[slug]`, MCP `instructions`, `frontend/public/llms-full.txt`, and the wiki API. New systems must surface in this fabric, not just in the database.

At minimum:

1. Add the system to `wiki/systems-catalog.md`. Pick the right category section (industry, trade, occupation, health, education, financial, regulatory, domain, geographic, etc.) and add one bullet with name, node count, and region/authority.

If the system fits an existing topical guide:

2. Extend the relevant page with a paragraph or table row. Examples:
   - Industry standard: `wiki/industry-classification.md`
   - Trade or product code system: `wiki/trade-codes.md`
   - Medical or health: `wiki/medical-coding.md`
   - Occupation or skills: `wiki/occupation-systems.md`
   - Geographic features: `wiki/categories-and-sectors.md` under geographic systems
   - New crosswalk topology: `wiki/crosswalk-map.md`

If the system opens a topic no existing wiki page covers (e.g., the first web vocabulary, the first lexical resource, the first financial ontology):

3. Add a new wiki page `wiki/<topic>.md` and register it in `wiki/_meta.json` with a unique `slug`, descriptive `title`, one-sentence `description`, and a fresh `order` value (one higher than the current max). Cross-link from any related existing pages.

The em-dash CI guard applies to wiki content. Use hyphens.

### Step 6 - Verify frontend routes

The `/codes` hub lists every system in the database. A new system's hub and deep-code pages must serve 200 on-demand.

**Rule.** `MAJOR_SYSTEMS` in `frontend/src/app/codes/constants.ts` is a **build-time scope list** (used by `generateStaticParams` and `sitemap.ts`), not a serve-time allowlist. The dynamic routes `/codes/[system]` and `/codes/[system]/[code]` MUST NOT hard-gate on `isMajorSystem()`. If you see a PR reintroduce such a gate, reject it - it 404s every non-curated system. Invalid system/code combos are caught by the existing `try/catch -> notFound()` around `serverGetNode` / `serverGetSystem`.

**Smoke test after ingest.** With the backend and frontend dev servers running:

```bash
SYSTEM=<new_system_id>
SAMPLE_CODE=<a top-level code you just ingested>
for url in \
  http://localhost:3001/codes/$SYSTEM \
  http://localhost:3001/codes/$SYSTEM/$SAMPLE_CODE; do
  echo "$(curl -s -o /dev/null -w '%{http_code}' "$url") $url"
done
```

Both must return 200. If either 404s, the route is gated - fix the route, not the data.

**When to add to `MAJOR_SYSTEMS`.** Only when the system is commercially significant enough to warrant pre-rendering its sector pages at build time (SEO priority). Most new systems do not need this - ISR serves them fine on first request.

### Step 7 - Regenerate AEO/RAG channels

After enrichment lands in the DB and the wiki has been updated, regenerate the public-facing static text artifacts so AI crawlers and the four-channel wiki distribution pick up the new system.

```bash
# llms-full.txt + llms.txt (driven by wiki/ content + system index)
python scripts/build_llms_txt.py

# llms-codes/ static dumps (driven by DB content)
# In dev, run via the seed helper to also commit + open a PR
bash scripts/seed_static_content.sh --push --pr
```

The pre-push hook also runs `build_static_content.py` and aborts the push if `llms-codes/` drifts from the DB, so a regen is enforced even if you forget. The weekly `static-content-refresh.yml` workflow opens drift PRs from the production DB as a final safety net.

If the system is large enough that the regen produces a multi-MB diff, consider a separate "regen" PR after the ingestion PR merges, rather than bundling both. See [Inclusion Policy](wiki/inclusion-policy.md) for related guidance on system size and subsetting.

### Step 8 - Commit

```bash
git add world_of_taxonomy/ingest/<system>.py tests/test_ingest_<system>.py
git add world_of_taxonomy/__main__.py CLAUDE.md DATA_SOURCES.md CHANGELOG.md
git add wiki/systems-catalog.md wiki/_meta.json wiki/<topic>.md
git add frontend/public/llms-full.txt frontend/public/llms.txt
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
- [ ] Descriptions enriched: SQL coverage check shows >= 99% (or documented lower target)
- [ ] Wiki updated: `systems-catalog.md` row added, topical guide extended, new page created if needed
- [ ] Full test suite passes: `python3 -m pytest tests/ -v`
- [ ] Frontend smoke test: `/codes/<new_system>` and `/codes/<new_system>/<code>` both return 200
- [ ] `llms-full.txt` + `llms.txt` regenerated
- [ ] `llms-codes/` regenerated (pre-push hook will catch drift if forgotten)

---

## Adding a Domain Deep-Dive Taxonomy

Follow Steps 0-8 above with these additions:

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
