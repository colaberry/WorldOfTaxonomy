# WorldOfTaxanomy

**Unified global industry classification knowledge graph.**

WorldOfTaxanomy connects 10 national and international industry classification systems as equal peers through crosswalk edges (equivalence mappings). It provides a REST API, MCP server for Claude Desktop, and a Next.js web app.

[![CI](https://github.com/colaberry/WorldOfTaxanomy/actions/workflows/ci.yml/badge.svg)](https://github.com/colaberry/WorldOfTaxanomy/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Systems

| System | Region | Codes |
|--------|--------|-------|
| NAICS 2022 | North America | 2,125 |
| NIC 2008 | India | 2,070 |
| SIC 1987 | USA/UK | 1,176 |
| NACE Rev 2 | European Union | 996 |
| WZ 2008 | Germany | 996 |
| ONACE 2008 | Austria | 996 |
| NOGA 2008 | Switzerland | 996 |
| ANZSIC 2006 | Australia/NZ | 825 |
| ISIC Rev 4 | Global (UN) | 766 |
| JSIC 2013 | Japan | 20 |

**10 systems. 10,966 codes. 11,420 crosswalk edges.**

---

## Quickstart

```bash
# Clone and install
git clone https://github.com/colaberry/WorldOfTaxanomy.git
cd WorldOfTaxanomy
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env and set DATABASE_URL and JWT_SECRET

# Start the API server
python3 -m uvicorn world_of_taxanomy.api.app:create_app --factory --port 8000

# Ingest a classification system
python3 -m world_of_taxanomy ingest naics

# Search
curl "http://localhost:8000/api/v1/search?q=truck+transportation"
```

---

## Architecture

```
WorldOfTaxanomy/
├── world_of_taxanomy/
│   ├── api/              # FastAPI REST API (19 endpoints)
│   │   ├── app.py        # App factory with lifespan pool management
│   │   ├── routers/      # systems, nodes, search, equivalences, explore, auth
│   │   └── schemas.py    # Pydantic response models
│   ├── mcp/              # MCP server (stdio, 20 tools)
│   │   └── server.py
│   ├── ingest/           # One ingester per classification system
│   ├── query/            # browse.py, search.py, equivalence.py
│   ├── db.py             # asyncpg pool (Neon PostgreSQL)
│   └── schema.sql        # classification_system, classification_node, equivalence
├── frontend/             # Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
├── tests/                # 277 tests, pytest, test_wot schema isolation
└── data/                 # Downloaded source files (not committed)
```

**Database:** Neon PostgreSQL (serverless). Three core tables:
- `classification_system` - one row per taxonomy
- `classification_node` - all codes across all systems
- `equivalence` - crosswalk edges between codes

---

## REST API

Base URL: `http://localhost:8000/api/v1` (or `https://worldoftaxanomy.com/api/v1`)

```
GET /systems                            List all classification systems
GET /systems/{id}                       System details with root codes
GET /systems/{id}/nodes/{code}          Get a specific code
GET /systems/{id}/nodes/{code}/children Child codes
GET /systems/{id}/nodes/{code}/ancestors Parent chain to root
GET /systems/{id}/nodes/{code}/equivalences Cross-system mappings
GET /systems/{id}/nodes/{code}/translations All equivalences in one call
GET /systems/{id}/nodes/{code}/siblings Sibling codes at same level
GET /systems/{id}/nodes/{code}/subtree  Summary stats for subtree
GET /search?q={query}                   Full-text search
GET /search?q={query}&grouped=true      Search grouped by system
GET /search?q={query}&context=true      Search with ancestors + children
GET /compare?a={sys}&b={sys}            Side-by-side sector comparison
GET /diff?a={sys}&b={sys}               Codes in A with no mapping to B
GET /nodes/{code}                       All systems containing a code
GET /systems/stats                      Leaf/total counts per system
GET /systems?group_by=region            Systems grouped by region
GET /equivalences/stats                 Crosswalk statistics
```

Authentication: `Authorization: Bearer wot_<your_key>` (optional, higher rate limits when provided)

---

## MCP Server (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "world-of-taxanomy": {
      "command": "/usr/bin/python3",
      "args": ["-m", "world_of_taxanomy", "mcp"],
      "env": {
        "DATABASE_URL": "your-database-url-here"
      }
    }
  }
}
```

Available tools (20): `list_systems`, `get_industry`, `browse_children`, `get_ancestors`, `search_classifications`, `get_equivalences`, `translate_code`, `get_sector_overview`, `translate_across_all_systems`, `compare_sector`, `find_by_keyword_all_systems`, `get_crosswalk_coverage`, `get_system_diff`, `get_siblings`, `get_subtree_summary`, `resolve_ambiguous_code`, `get_leaf_count`, `get_region_mapping`, `describe_match_types`, `explore_industry_tree`

---

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Tests use a `test_wot` PostgreSQL schema isolated from production data. Never touches the `public` schema.

---

## Adding a New Classification System

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full step-by-step guide.

Short version:
1. Create `world_of_taxanomy/ingest/<system>.py` with `ingest_<system>(conn, path=None) -> int`
2. Create `tests/test_ingest_<system>.py` with unit tests (TDD - RED first)
3. Register in `world_of_taxanomy/__main__.py`
4. Update `CLAUDE.md`, `data/README.md`, `CHANGELOG.md`

---

## Data Sources

See [DATA_SOURCES.md](DATA_SOURCES.md) for full license and attribution information for each classification system.

---

## License

MIT License. See [LICENSE](LICENSE).

Classification data is sourced from public domain and open license sources. See DATA_SOURCES.md for per-system licensing.
