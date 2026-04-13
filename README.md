# WorldOfTaxanomy

**The world's most comprehensive open taxonomy knowledge graph.**

WorldOfTaxanomy federates 88 classification systems - industry, geography, product, trade, occupation, education, health, regulation, emerging sectors, and domain deep-dives - into a single queryable knowledge graph. Every code in every system can be translated to its equivalents in every other system through crosswalk edges.

[![CI](https://github.com/colaberry/WorldOfTaxanomy/actions/workflows/ci.yml/badge.svg)](https://github.com/colaberry/WorldOfTaxanomy/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What is this?

Every country, industry body, and international organization has its own classification system. A truck driver in the US is NAICS 484, SOC 53-3032, ISCO-08 8332, ESCO occ/transport-worker - four different codes in four different systems that all mean the same thing.

WorldOfTaxanomy is the Rosetta Stone that connects them all.

**88 systems. ~538,000 codes. ~57,760 crosswalk edges.**

---

## Systems

### Industry Classification

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| NAICS 2022 | North America | 2,125 | North American Industry Classification System |
| ISIC Rev 4 | Global (UN) | 766 | International Standard Industrial Classification |
| NACE Rev 2 | European Union | 996 | EU statistical classification of economic activities |
| SIC 1987 | USA/UK | 1,176 | Standard Industrial Classification |
| ANZSIC 2006 | Australia/NZ | 825 | Australian and NZ Standard Industrial Classification |
| NIC 2008 | India | 2,070 | National Industrial Classification |
| WZ 2008 | Germany | 996 | Klassifikation der Wirtschaftszweige |
| ONACE 2008 | Austria | 996 | Osterreichische Systematik der Wirtschaftstatigkeiten |
| NOGA 2008 | Switzerland | 996 | Nomenclature generale des activites economiques |
| JSIC 2013 | Japan | 20 | Japan Standard Industrial Classification |

### Geography

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| ISO 3166-1 | Global | 271 | Countries with UN M.49 regional hierarchy |
| ISO 3166-2 | Global | 5,246 | Country subdivisions (states, provinces, regions) |
| UN M.49 | Global | 272 | UN geographic regions and sub-regions |

### Product and Trade

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| HS 2022 | Global (WCO) | 6,960 | Harmonized System for international trade |
| CPC v2.1 | Global (UN) | 4,596 | Central Product Classification |
| UNSPSC v24 | Global (GS1 US) | 77,337 | Universal Standard Products and Services Code |

### Occupational

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| SOC 2018 | United States | 1,447 | Standard Occupational Classification |
| ISCO-08 | Global (ILO) | 619 | International Standard Classification of Occupations |
| ANZSCO 2022 | Australia/NZ | ~1,590 | Australian and NZ Standard Classification of Occupations |
| ESCO Occupations | Europe / Global | ~2,942 | European Skills, Competences, Qualifications and Occupations |
| O*NET-SOC | United States | ~867 | Occupational Information Network |

### Education

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| CIP 2020 | United States | 2,848 | Classification of Instructional Programs |
| ISCED 2011 | Global (UNESCO) | 20 | International Standard Classification of Education |
| ISCED-F 2013 | Global (UNESCO) | 122 | ISCED Fields of Education and Training |

### Health and Clinical

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| ATC WHO 2021 | Global (WHO) | 6,440 | Anatomical Therapeutic Chemical classification |
| ICD-11 MMS | Global (WHO) | 37,052 | International Classification of Diseases 11th Revision |
| LOINC | Global (Regenstrief) | ~102,751 | Logical Observation Identifiers Names and Codes |

### Financial, Environmental, and Skills

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| COFOG | Global (UN) | 188 | Classification of Functions of Government |
| GICS Bridge | Global (MSCI/S&P) | 11 | Global Industry Classification Standard (11 public sectors) |
| GHG Protocol | Global (WRI/WBCSD) | 20 | Greenhouse Gas Protocol scope 1/2/3 categories |
| ESCO Skills | Europe / Global | ~13,890 | ESCO skills and competences taxonomy |
| Patent CPC | Global (EPO/USPTO) | ~260,000 | Cooperative Patent Classification |

### Regulatory

| System | Region | Codes | Description |
|--------|--------|-------|-------------|
| CFR Title 49 | United States | 104 | Code of Federal Regulations (Transportation) |
| FMCSA Regulations | United States | 80 | Federal Motor Carrier Safety Administration rules |
| GDPR Articles | European Union | 110 | General Data Protection Regulation articles |
| ISO 31000 | Global (ISO) | 47 | Risk Management Guidelines |

### Domain Deep-Dives (20 NAICS sectors covered)

Sub-industry vocabularies that attach below a classification node and provide structured detail not available in top-level systems.

| Sector | Domain Taxonomies |
|--------|-------------------|
| Truck Transportation (484) | freight types, vehicle classes, cargo, carrier operations |
| Agriculture (11) | crop types, livestock categories, farming methods, commodity grades |
| Mining (21) | mineral types, extraction methods, reserve classification |
| Utilities (22) | energy sources, grid regions |
| Construction (23) | trade types, building types |
| Manufacturing (31-33) | process types |
| Retail (44-45) | channel types |
| Finance (52) | instrument types |
| Healthcare (62) | care settings |
| Transportation - other (48-49) | transport modes |
| Information (51) | media types |
| Real Estate (53) | property types |
| Food Service (72) | service types |
| Wholesale (42) | trade channels |
| Professional Services (54) | service types |
| Education (61) | program types |
| Arts (71) | content types |
| Other Services (81) | service types |
| Public Administration (92) | admin types |
| Cross-sector | supply chain terms, workforce safety |

### Magna Compass Emerging Sectors

Structured domain vocabularies for the 12 emerging investment sectors defined in the Magna Compass 2026 R2 Global Industry Blueprint, plus 3 CORE gaps:

| Domain | Codes | Description |
|--------|-------|-------------|
| AI and Data Types | 25 | Foundation models, data infrastructure, AI verticals, MLOps |
| Biotechnology and Genomics | 26 | Drug discovery, genomics, cell/gene therapy, biomanufacturing |
| Space and Satellite Economy | 24 | Launch vehicles, satellite types, downstream applications |
| Climate Technology | 30 | Solar, wind, green hydrogen, CCUS, carbon markets, EVs |
| Advanced Materials | 27 | Composites, biomaterials, nanomaterials, smart materials |
| Quantum Computing | 23 | Qubit technologies, error correction, quantum networking |
| Digital Assets and Web3 | 25 | Layer 1/2 blockchains, DeFi, NFTs, stablecoins, CBDC |
| Autonomous Systems and Robotics | 27 | Industrial, collaborative, mobile, drone, humanoid robots |
| New Energy Storage | 25 | Li-ion, solid-state, flow batteries, grid-scale, hydrogen |
| Next-Generation Semiconductors | 31 | Logic, memory, analog, power, photonics, packaging |
| Synthetic Biology | 28 | Metabolic engineering, CRISPR, cell-free, cultured meat |
| Extended Reality and Metaverse | 27 | VR, AR, MR, spatial computing, metaverse platforms |
| Chemical Industry Types | 29 | Petrochemicals, specialty chemicals, polymers, gases |
| Defence and Security Types | 23 | Land, naval, air/space systems, cyber, intelligence |
| Water and Environment Types | 28 | Treatment, distribution, wastewater, desalination |

---

## Country Taxonomy Profile

WorldOfTaxanomy knows which classification systems apply to each country:

```bash
# Which classification systems apply to Germany?
curl "http://localhost:8000/api/v1/countries/DE"
# Returns: WZ 2008 (official), NACE Rev 2 (regional), ISIC Rev 4 (recommended)

# Which systems apply to Pakistan?
curl "http://localhost:8000/api/v1/countries/PK"
# Returns: ISIC Rev 4 (recommended) + sector strengths from geo-sector crosswalk

# Filter all systems by country
curl "http://localhost:8000/api/v1/systems?country=AU"
# Returns: ANZSIC 2006 (official) + ISIC Rev 4 (recommended)

# Bulk stats for world map visualization
curl "http://localhost:8000/api/v1/countries/stats"
```

249 countries covered via the `country_system_link` table with relevance values: `official` | `regional` | `recommended` | `historical`.

---

## Quickstart

```bash
# Clone and install
git clone https://github.com/colaberry/WorldOfTaxanomy.git
cd WorldOfTaxanomy
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env: set DATABASE_URL (Neon PostgreSQL) and JWT_SECRET

# Initialize the database schema
python3 -m world_of_taxanomy init

# Ingest core industry systems
python3 -m world_of_taxanomy ingest naics
python3 -m world_of_taxanomy ingest isic
python3 -m world_of_taxanomy ingest crosswalk

# Ingest everything (takes ~30 minutes, some systems require manual download)
python3 -m world_of_taxanomy ingest all

# Start the API server
python3 -m uvicorn world_of_taxanomy.api.app:create_app --factory --port 8000

# Start the MCP server (for Claude Desktop)
python3 -m world_of_taxanomy mcp

# Start the frontend (requires Node.js)
cd frontend && npx next dev --port 3000
```

### Try the API

```bash
# Search across all systems
curl "http://localhost:8000/api/v1/search?q=truck+transportation"

# Translate a NAICS code to all equivalent systems
curl "http://localhost:8000/api/v1/systems/naics_2022/nodes/4841/translations"

# Country taxonomy profile
curl "http://localhost:8000/api/v1/countries/DE"

# System stats
curl "http://localhost:8000/api/v1/systems/stats"
```

---

## Architecture

```
WorldOfTaxanomy/
├── world_of_taxanomy/
│   ├── api/              # FastAPI REST API
│   │   ├── app.py        # App factory with lifespan pool management
│   │   ├── routers/      # systems, nodes, search, equivalences, countries, auth
│   │   └── schemas.py    # Pydantic response models
│   ├── mcp/              # MCP server (stdio transport, 21 tools)
│   │   ├── server.py
│   │   ├── protocol.py   # JSON-RPC handler
│   │   └── handlers.py   # Tool handler functions
│   ├── ingest/           # One ingester per classification system (80+ files)
│   │   ├── base.py       # ensure_data_file() download utility
│   │   ├── naics.py      # NAICS 2022
│   │   ├── isic.py       # ISIC Rev 4
│   │   ├── domain_*.py   # 36 domain deep-dive taxonomies
│   │   └── crosswalk_*.py # 20+ crosswalk ingesters
│   ├── query/            # Query layer (browse, search, equivalence)
│   ├── db.py             # asyncpg pool (Neon PostgreSQL)
│   ├── schema.sql        # classification_system, classification_node, equivalence,
│   │                     # domain_taxonomy, node_taxonomy_link, country_system_link
│   └── schema_auth.sql   # app_user, api_key, usage_log
├── frontend/             # Next.js 16 + TypeScript + Tailwind CSS + shadcn/ui
│   └── src/
│       ├── app/          # Home (world map), Explore, System detail, Dashboard, Node detail
│       └── components/
│           └── visualizations/  # WorldMap (D3 geo), GalaxyView (D3 force), SectorTreemap
├── tests/                # 1,876 tests, pytest, test_wot schema isolation
└── data/                 # Downloaded source files (gitignored, re-downloadable)
```

### Database schema

```sql
classification_system      -- one row per taxonomy (88 rows)
classification_node        -- all codes across all systems (~538K rows)
equivalence                -- crosswalk edges between codes (~57,760 rows)
domain_taxonomy            -- registers domain sub-taxonomies
node_taxonomy_link         -- links industry nodes to domain concepts
country_system_link        -- maps ISO 3166-1 country codes to applicable systems
```

---

## REST API

Base URL: `http://localhost:8000/api/v1`

```
GET /systems                                    List all 88 classification systems
GET /systems?country={code}                     Systems applicable to a country
GET /systems/{id}                               System details with root codes
GET /systems/{id}/nodes/{code}                  Get a specific code
GET /systems/{id}/nodes/{code}/children         Child codes
GET /systems/{id}/nodes/{code}/ancestors        Parent chain to root
GET /systems/{id}/nodes/{code}/equivalences     Cross-system mappings
GET /systems/{id}/nodes/{code}/translations     All equivalences in one call
GET /systems/{id}/nodes/{code}/siblings         Sibling codes at same level
GET /systems/{id}/nodes/{code}/subtree          Summary stats for subtree
GET /search?q={query}                           Full-text search across all systems
GET /search?q={query}&grouped=true              Search results grouped by system
GET /compare?a={sys}&b={sys}                    Side-by-side sector comparison
GET /diff?a={sys}&b={sys}                       Codes in A with no mapping to B
GET /systems/stats                              Code counts per system
GET /equivalences/stats                         Crosswalk edge statistics
GET /countries/stats                            Per-country taxonomy coverage (world map)
GET /countries/{code}                           Full taxonomy profile for a country
```

Authentication: `Authorization: Bearer wot_<your_key>` (optional, higher rate limits)

---

## MCP Server (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "world-of-taxanomy": {
      "command": "python3",
      "args": ["-m", "world_of_taxanomy", "mcp"],
      "env": {
        "DATABASE_URL": "your-neon-database-url"
      }
    }
  }
}
```

**21 MCP tools available:**

| Tool | Description |
|------|-------------|
| `list_classification_systems` | List all 88 systems |
| `get_industry` | Get details for a specific code |
| `browse_children` | Get direct children of a code |
| `get_ancestors` | Get path from root to a code |
| `search_classifications` | Full-text search across all systems |
| `get_equivalences` | Cross-system equivalences for a code |
| `translate_code` | Translate a code to another system |
| `get_sector_overview` | Top-level sectors for a system |
| `translate_across_all_systems` | Translate a code to every other system |
| `compare_sector` | Side-by-side root nodes for two systems |
| `find_by_keyword_all_systems` | Search grouped by system |
| `get_crosswalk_coverage` | Per-pair edge counts |
| `get_system_diff` | Codes in A with no mapping to B |
| `get_siblings` | Sibling codes at same parent level |
| `get_subtree_summary` | Aggregate stats under a code |
| `resolve_ambiguous_code` | Find all systems containing a code |
| `get_leaf_count` | Leaf and total node counts per system |
| `get_region_mapping` | Systems grouped by region |
| `describe_match_types` | Definitions of exact/partial/broad/narrow |
| `explore_industry_tree` | Search with ancestors and children context |
| `get_country_taxonomy_profile` | Classification systems for a country + sector strengths |

---

## Running Tests

```bash
# Full suite (1,876 tests)
python3 -m pytest tests/ -v

# Specific system
python3 -m pytest tests/test_ingest_naics.py -v

# With coverage
python3 -m pytest tests/ --cov=world_of_taxanomy
```

Tests use a `test_wot` PostgreSQL schema isolated from production data.

---

## Adding a New Classification System

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Short version:

1. Write failing tests first (`tests/test_ingest_<system>.py`) - TDD is mandatory
2. Create `world_of_taxanomy/ingest/<system>.py` with `async def ingest_<system>(conn) -> int`
3. Register in `world_of_taxanomy/__main__.py`
4. Update `CLAUDE.md`, `DATA_SOURCES.md`, `CHANGELOG.md`

---

## Extending for a New Country Profile

To add country-system mappings for new countries or update existing relevance classifications:

```python
# world_of_taxanomy/ingest/crosswalk_country_system.py
COUNTRY_SYSTEM_LINKS = [
    # (country_code, system_id, relevance, notes)
    ("XY", "isic_rev4", "recommended", "UN global standard"),
    ("XY", "my_national_system", "official", "National classification body"),
]
```

Relevance values: `official` | `regional` | `recommended` | `historical`

Run: `python3 -m world_of_taxanomy ingest crosswalk_country_system`

---

## Extending for a New Emerging Sector

To add a new domain deep-dive taxonomy (e.g. for a new industry vertical):

```python
# world_of_taxanomy/ingest/domain_<sector>.py
_DOMAIN_ROW = ("domain_<sector>", "Display Name", "Full Name", "WorldOfTaxanomy", None)
NODES = [
    ("dxx_cat", "Category Name", 1, None),
    ("dxx_cat_type", "Specific Type", 2, "dxx_cat"),
]
_NAICS_PREFIXES = ["XXX"]  # NAICS codes to link via node_taxonomy_link

async def ingest_domain_<sector>(conn) -> int:
    ...
```

See `world_of_taxanomy/ingest/domain_ai_data.py` as the canonical reference for an emerging sector taxonomy.

---

## Domain Deep-Dive Query Pattern

```sql
-- All AI/Data domain concepts linked to a NAICS software node
SELECT n.code, n.title, tl.taxonomy_id
FROM classification_node n
JOIN node_taxonomy_link tl
  ON tl.node_code = n.code AND tl.system_id = n.system_id
WHERE n.system_id = 'naics_2022' AND n.code LIKE '5415%'
ORDER BY n.code;

-- Country taxonomy profile
SELECT cs.name, csl.relevance, csl.notes
FROM country_system_link csl
JOIN classification_system cs ON cs.id = csl.system_id
WHERE csl.country_code = 'DE'
ORDER BY CASE csl.relevance WHEN 'official' THEN 1 WHEN 'regional' THEN 2 WHEN 'recommended' THEN 3 ELSE 4 END;
```

---

## Data Sources

See [DATA_SOURCES.md](DATA_SOURCES.md) for full attribution and license information.

WorldOfTaxanomy does not redistribute raw data files. Each ingester downloads data directly from the authoritative source at ingest time (or requires manual placement in `data/` where license terms prohibit automated access).

---

## License

MIT License. See [LICENSE](LICENSE).

Classification data is sourced from public domain and open license sources. See [DATA_SOURCES.md](DATA_SOURCES.md) for per-system licensing.
