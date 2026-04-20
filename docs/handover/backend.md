# Backend Drill-Down

FastAPI app + MCP server + ingest pipeline + wiki loader. Reads [HANDOVER.md](../../HANDOVER.md) first for the overall picture.

---

## App factory and lifespan

[world_of_taxonomy/api/app.py](../../world_of_taxonomy/api/app.py) exposes `create_app()` (a factory so uvicorn's `--factory` flag can call it). The lifespan context manager:

1. Opens the asyncpg pool via `get_pool()` from [world_of_taxonomy/db.py](../../world_of_taxonomy/db.py) and stashes it on `app.state.pool`.
2. Registers middleware (CORS, rate-limit, error handler).
3. Includes every router from [world_of_taxonomy/api/routers/](../../world_of_taxonomy/api/routers/). Order matters: `explore` is included before `systems` to avoid `/systems/stats` being eaten by the `/systems/{id}` dynamic route.
4. On shutdown, closes the pool.

```
create_app()
 ├─ validate_required_env()       # refuse to boot on missing/weak vars
 ├─ lifespan open -> get_pool() -> app.state.pool  (connect retry + env pool sizing)
 ├─ CORS middleware (ALLOWED_ORIGINS allowlist; defaults closed)
 ├─ security_headers_middleware   # HSTS, nosniff, frame-deny, referrer, permissions
 ├─ request_id_middleware         # propagate X-Request-ID
 ├─ json_access_log_middleware    # one JSON line per request
 ├─ body_size_limit_middleware    # 2 MiB cap
 ├─ GZipMiddleware (min_size=500)
 ├─ metrics_middleware            # wot_http_* counters + latency + in-flight
 ├─ rate_limit_middleware         # tier-aware + X-RateLimit-* headers
 ├─ include_router(systems, nodes, search, equivalences, explore,
 │                 countries, classify, auth, oauth, wiki, contact,
 │                 audit, export, bulk_export, crosswalk_graph,
 │                 metrics, healthz, version, honeypot, csp_report, canary)
 └─ lifespan close -> graceful uvicorn drain -> pool.close()
```

---

## asyncpg pool and the pgbouncer gotcha

[world_of_taxonomy/db.py](../../world_of_taxonomy/db.py) reads `DATABASE_URL` at import time and creates an asyncpg pool with `min_size=2`, `max_size=10`, `command_timeout=30`.

**Critical constraint**: when a pgbouncer-style pooler sits in transaction-pooling mode between the app and Postgres, it does not keep a 1:1 session with the backend, so server-side prepared statements (asyncpg's default for caching query plans) break. Set `statement_cache_size=0` when that is your topology. The test pool already does this in [tests/conftest.py](../../tests/conftest.py).

Providers this applies to: Neon (always), Supabase via the pooled URL, any self-hosted pgbouncer in transaction mode. If you connect directly to Postgres (no pooler, or a session-mode pooler), you can drop the setting.

---

## Dependency injection graph

[world_of_taxonomy/api/deps.py](../../world_of_taxonomy/api/deps.py):

| Dep | Returns | Raises |
|-----|---------|--------|
| `get_conn(request)` | `asyncpg.Connection` from `app.state.pool` (yields then releases) | - |
| `get_current_user(request)` | `dict` of user fields from JWT claims | `401` if missing/invalid/expired |
| `get_optional_auth(request)` | user dict or `None` | never |
| `validate_api_key(pool, raw_key)` | user dict | `401` on mismatch |

`get_optional_auth` is what lets the rate limiter know which tier to apply. `DISABLE_AUTH=true` makes `get_current_user` return a synthetic dev user instead of raising - dev-only.

JWT: HS256, 15-minute access tokens, secret from `JWT_SECRET` (validated >=32 chars in prod startup path).

API key format: literal `wot_` + 32 hex characters = 36 chars total. Storage is bcrypt of the whole string, plus an indexed 8-char `key_prefix` (the first 8 hex chars after `wot_`) so lookup is a single btree seek followed by one bcrypt compare against the full key.

---

## Rate-limit middleware

[world_of_taxonomy/api/middleware.py](../../world_of_taxonomy/api/middleware.py) combines slowapi with a custom tier-aware layer:

| Tier | Per minute | Per day |
|------|-----------:|--------:|
| Anonymous | 30 | 1,000 |
| Free | 100 | 5,000 |
| Pro | 1,000 | 100,000 |
| Enterprise | 10,000 | unlimited |

On every successful response (`status < 400`), the middleware upserts into `daily_usage` (one row per `user_id` / `usage_date`). Full audit trail is written to `usage_log` with `endpoint`, `method`, `status_code`, and `ip_address`. Indexed on `(user_id, created_at)` so per-user reporting is cheap.

---

## Router inventory

From [world_of_taxonomy/api/routers/](../../world_of_taxonomy/api/routers/):

| Router | Key routes | Auth |
|--------|------------|------|
| `systems` | `GET /systems`, `GET /systems/{id}` | optional |
| `nodes` | `GET /systems/{id}/nodes/{code}`, `/children`, `/ancestors`, `/siblings`, `/subtree`, `/equivalences`, `/translations` | optional |
| `search` | `GET /search?q=&system=&grouped=&context=` | optional |
| `equivalences` | `GET /equivalences`, `GET /equivalences/stats` | optional |
| `explore` | `GET /explore/stats`, `/systems/stats`, `/compare`, `/diff` | optional |
| `countries` | `GET /countries`, `/countries/{code}`, `/countries/stats` | optional |
| `classify` | `POST /classify` - free text to codes across all systems | Pro+ (LLM fallback requires `OLLAMA_API_KEY` or `OPENROUTER_API_KEY`) |
| `auth` | `POST /register`, `/login`, `GET /me`, `/api-keys` CRUD | varies |
| `oauth` | `GET /auth/oauth/{provider}/authorize`, callback | none |
| `wiki` | `GET /wiki`, `GET /wiki/{slug}` | optional |
| `contact` | `POST /contact` - form delivery | none |
| `audit`, `export`, `bulk_export`, `crosswalk_graph` | admin + export utilities | mixed |
| `metrics` | `GET /api/v1/metrics` (Prometheus exposition) | `METRICS_TOKEN` header |
| `healthz` | `GET /api/v1/healthz` - uptime probe, no DB hit | none |
| `version` | `GET /api/v1/version` - git sha + build time | none |
| `csp_report` | `POST /api/v1/csp-report` - CSP violation sink | none |
| `honeypot` | decoy paths + `/.well-known/security.txt` | none |
| `canary` | canary token endpoints used by `llms-full.txt` embeds | none |

Search ranking (see [world_of_taxonomy/api/routers/search.py](../../world_of_taxonomy/api/routers/search.py)) uses the GIN-indexed `tsvector` with `plainto_tsquery` and falls back to `ILIKE` when the tsquery returns zero rows. Results are ranked by `ts_rank` then `seq_order`.

---

## Security and ops modules

Beyond auth and rate-limit, the backend ships a set of cross-cutting modules in [world_of_taxonomy/api/](../../world_of_taxonomy/api/):

| Module | Purpose |
|--------|---------|
| `security_headers.py` | Applies HSTS, nosniff, frame-deny, Referrer-Policy, Permissions-Policy on every response. |
| `metrics.py` | Prometheus counters + latency histogram + in-flight gauge. Bounded cardinality on route templates. |
| `healthz.py`, `version.py` | Liveness probe + build-info endpoint. |
| `honeypot.py` | Decoy paths (`/wp-admin`, `/.env`, etc.) + RFC 9116 `security.txt`. |
| `csp_report.py` | CSP violation sink; counter keyed on known directives, everything else bucketed as `other`. |
| `canary.py` | Tracks hits on canary tokens seeded into `llms-full.txt`. |
| `failed_auth.py` | Sliding-window per-IP + per-email login failure counters. |
| `text_guard.py` | NFKC-normalizes + regex-filters `/classify` input for prompt-injection defense. |
| `request_id.py` | Generates or propagates `X-Request-ID` for log correlation. |
| `access_log.py` | One JSON log line per HTTP request. |
| `env_validation.py` | Fails fast at boot when required env vars are missing or weak. |

Optional Sentry telemetry (`SENTRY_DSN`) is initialized in `app.py` before middleware so unhandled errors propagate correctly.

Ingest-side sanity: [world_of_taxonomy/ingest/validators.py](../../world_of_taxonomy/ingest/validators.py) runs post-load checks (orphaned nodes, level-1 roots, parent-child cycle detection, duplicate codes).

Schema evolution uses Alembic (psycopg v3 driver) under [migrations/](../../migrations/); the baseline revision captures `schema.sql` + `schema_auth.sql` as of HANDOVER creation.

---

## MCP server

[world_of_taxonomy/mcp/server.py](../../world_of_taxonomy/mcp/server.py) runs a stdio JSON-RPC loop: newline-delimited JSON in, newline-delimited JSON out. Errors go to stderr so host loggers can separate them.

[world_of_taxonomy/mcp/protocol.py](../../world_of_taxonomy/mcp/protocol.py) builds the `initialize` response:
- `tools` array: JSON Schemas for all 25 tools (navigation, search, crosswalk translation, stats, geography, classification).
- `instructions`: output of `build_wiki_context()` from [world_of_taxonomy/wiki.py](../../world_of_taxonomy/wiki.py) - concatenates the priority wiki slugs (`getting-started`, `systems-catalog`, `crosswalk-map`, `industry-classification`, `categories-and-sectors`) capped at ~10-15K tokens.

[world_of_taxonomy/mcp/handlers.py](../../world_of_taxonomy/mcp/handlers.py) delegates each tool call to the same query functions the REST API uses (`query.browse`, `query.search`, `query.equivalence`, `query.provenance`), then decorates the response with provenance metadata (authority, license, source URL) from `get_system_provenance_map()`.

Tools include: `list_classification_systems`, `get_industry`, `browse_children`, `get_ancestors`, `get_siblings`, `search_classifications`, `resolve_ambiguous_code`, `find_by_keyword_all_systems`, `get_equivalences`, `translate_code`, `translate_across_all_systems`, `compare_sector`, `get_system_diff`, `get_sector_overview`, `get_crosswalk_coverage`, `list_crosswalks_by_kind`, `describe_match_types`, `explore_industry_tree`, `get_leaf_count`, `get_subtree_summary`, `get_audit_report`, `get_region_mapping`, `get_country_taxonomy_profile`, `get_country_scope`, `classify_business`.

Equivalences returned by `get_equivalences`, `translate_code`, `translate_across_all_systems`, and `list_crosswalks_by_kind` carry an `edge_kind` label (`standard_standard`, `standard_domain`, `domain_domain`) plus `source_category`/`target_category` for UI grouping; see [world_of_taxonomy/category.py](../../world_of_taxonomy/category.py) for `compute_edge_kind()`.

Entry points: `python -m world_of_taxonomy mcp`, or via the wrapper script [run_mcp.sh](../../run_mcp.sh) that activates the virtualenv first.

---

## Ingest pipeline

~873 files in [world_of_taxonomy/ingest/](../../world_of_taxonomy/ingest/). One module per system plus:

- [ingest/base.py](../../world_of_taxonomy/ingest/base.py) - `ensure_data_file(url, local_path)` and `ensure_data_file_zip(url, local_path, member)`. Both cache downloads on disk, set a `WorldOfTaxonomy/0.1` User-Agent, and disable SSL cert verification because a handful of government sites ship expired chains.
- Per-system modules expose `ingest()`. Internal shape varies because every upstream source is a different kind of awful (XLS for ABS, XLSX for Eurostat, CSV for Census, HTML tables for OSHA, PDF for NIC, hand-curated Python literals for domain vocabularies).

### Representative patterns

- **NAICS 2022** ([ingest/naics.py](../../world_of_taxonomy/ingest/naics.py)): Parses the Census Bureau Excel; level is `len(code) - 1`; the 31-33 range sector is handled via an explicit `NAICS_SECTOR_MAP`.
- **NACE Rev 2** ([ingest/nace.py](../../world_of_taxonomy/ingest/nace.py)): Built from the ISIC4<->NACE2 concordance. Levels: section (A-Z), division (2-digit), group (`XX.X`), class (`XX.XX`). `match_type` is `partial` if the concordance has any part flag, else `exact`.
- **NACE-derived** (`nace_derived.py` - WZ 2008, ÖNACE 2008, NOGA 2008): Copy all NACE nodes and write 1:1 equivalence edges. Structural derivation, not an independent ingest - flagged as `structural_derivation` in `data_provenance`.
- **Domain vocabularies** (e.g. `domain_truck_freight.py`): Hand-curated literals with `expert_curated` provenance. They also write `node_taxonomy_link` rows to bind domain terms to anchor codes like "NAICS 484."

### Dispatcher

[world_of_taxonomy/__main__.py](../../world_of_taxonomy/__main__.py) is a massive if/elif wall mapping CLI targets to ingester modules. Subcommands:

| Command | What it does |
|---------|--------------|
| `init` | Create core schema ([schema.sql](../../world_of_taxonomy/schema.sql)) |
| `init-auth` | Create auth schema ([schema_auth.sql](../../world_of_taxonomy/schema_auth.sql)) |
| `reset` | Drop all tables (local only - guards against prod DATABASE_URL) |
| `ingest <target>` | Run one ingester (`naics`, `isic`, `nace`, ..., `all`, `all-crosswalks`, `all-domains`) |
| `serve` | Launch uvicorn on the API |
| `mcp` | Launch the stdio MCP server |
| `browse`, `search`, `equiv`, `stats` | CLI read commands |

Adding a system is a TDD exercise; the canonical 7-step recipe lives in [CONTRIBUTING.md](../../CONTRIBUTING.md) and the long-form walkthrough is [docs/adding-a-new-system.md](../adding-a-new-system.md).

---

## Wiki loader

[world_of_taxonomy/wiki.py](../../world_of_taxonomy/wiki.py):

| Function | Purpose |
|----------|---------|
| `load_wiki_meta()` | Parses [wiki/_meta.json](../../wiki/_meta.json) for slug ordering and titles |
| `load_wiki_page(slug)` | Returns raw markdown by slug |
| `load_all_wiki_pages()` | `{slug: markdown}` for every page |
| `build_wiki_context()` | Concatenates priority slugs for the MCP `initialize` response; respects a token budget |
| `build_llms_full_txt()` | Concatenates all wiki pages in `_meta.json` order for the crawler file |
| `get_system_provenance_map()` | `{system_id: {authority, license, source_url}}` used by MCP handlers to decorate responses |

[scripts/build_llms_txt.py](../../scripts/build_llms_txt.py) calls `build_llms_full_txt()` and writes [frontend/public/llms-full.txt](../../frontend/public/llms-full.txt). Run after any wiki edit. CI does NOT auto-regenerate; commits with out-of-date `llms-full.txt` are your problem to catch.

---

## Tests

[tests/conftest.py](../../tests/conftest.py):

- Session-scoped `db_pool` fixture: drops and recreates a `test_wot` Postgres schema, sets `search_path=test_wot, public` on every connection via `init` callback.
- `statement_cache_size=0` (pgbouncer).
- Autouse `setup_and_teardown` truncates tables between tests.
- Tests marked `@pytest.mark.cli` skip the DB setup.

Representative suites:
- `test_api_*.py` - contract tests for each router.
- `test_auth.py` - hashing, JWT, API keys, rate limits.
- `test_mcp_*.py` - protocol envelope + per-tool handler.
- `test_ingest_*.py` - one per system; validates parsed node counts and level distributions against published authority totals.
- `test_node_detail_contract.py` - golden test for the node detail API shape (the frontend is tightly coupled to this).

Run: `python3 -m pytest tests/ -v`. Single file: `pytest tests/test_ingest_naics.py -v`.

---

## Non-obvious rules

1. **Statement cache**: `statement_cache_size=0` on any pool that sits behind a pgbouncer-style pooler in transaction mode (Neon, Supabase pooled URL, self-hosted pgbouncer). Direct connections don't need it.
2. **JWT secret length**: >=32 chars in prod. The dev default is intentionally shorter so production can't silently adopt it.
3. **Em-dash ban**: CI greps `*.py`, `*.md`, `*.ts`, `*.tsx`, `*.sql` for U+2014 and fails on any match. See [.github/workflows/ci.yml](../../.github/workflows/ci.yml).
4. **Test schema isolation**: tests MUST run in `test_wot`. Never point tests at `public`.
5. **TDD**: red first, then green, then refactor. Never write implementation without a failing test.
6. **No speculative code**: don't add features, abstractions, or error handling the task doesn't require.
7. **Provenance honesty**: use `structural_derivation` when copying another system's tree (WZ, ÖNACE, NOGA from NACE). Use `expert_curated` for hand-written domain vocabularies. `official_download` is reserved for data fetched verbatim from the authority.
8. **Crosswalk match types**: `exact` (1:1), `partial` (split codes), `broad` (target is a superset), `narrow` (target is a subset). Never guess - use what the upstream concordance says.
