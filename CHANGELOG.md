# Changelog

All notable changes to WorldOfTaxanomy are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- ISO 3166-1 Countries ingester (`iso_3166_1`, 271 nodes: 5 continents, 17 sub-regions, 249 countries) - Phase 1-A
- ISO 3166-2 Subdivisions ingester (`iso_3166_2`, ~5,246 nodes: 200 country stubs + ~5,046 subdivisions) - Phase 1-B
- ISO 3166 crosswalk (`crosswalk_iso3166`, ~498 edges linking iso_3166_1 to iso_3166_2) - Phase 1-C
- UN M.49 Geographic Regions ingester (`un_m49`, ~272 nodes: World, 5 regions, 24 sub-regions, ~249 countries) - Phase 1-D

---

## [0.1.0] - 2026-04-07

### Added

**10 classification systems ingested:**
- NAICS 2022 (North America, 2,125 codes)
- ISIC Rev 4 (Global/UN, 766 codes)
- NACE Rev 2 (European Union, 996 codes)
- SIC 1987 (USA/UK, 1,176 codes)
- ANZSIC 2006 (Australia/NZ, 825 codes)
- NIC 2008 (India, 2,070 codes)
- WZ 2008 (Germany, 996 codes - derived from NACE Rev 2)
- ONACE 2008 (Austria, 996 codes - derived from NACE Rev 2)
- NOGA 2008 (Switzerland, 996 codes - derived from NACE Rev 2)
- JSIC 2013 (Japan, 20 division codes)

**REST API (FastAPI, 19 endpoints):**
- `/api/v1/systems` - list and group systems
- `/api/v1/systems/{id}` - system detail with roots
- `/api/v1/systems/{id}/nodes/{code}` - node detail
- `/api/v1/systems/{id}/nodes/{code}/children` - child nodes
- `/api/v1/systems/{id}/nodes/{code}/ancestors` - ancestor chain
- `/api/v1/systems/{id}/nodes/{code}/equivalences` - crosswalk edges
- `/api/v1/systems/{id}/nodes/{code}/translations` - all equivalences at once
- `/api/v1/systems/{id}/nodes/{code}/siblings` - sibling nodes
- `/api/v1/systems/{id}/nodes/{code}/subtree` - subtree summary stats
- `/api/v1/search` - full-text search (with grouped and context modes)
- `/api/v1/compare` - side-by-side sector comparison
- `/api/v1/diff` - codes with no mapping to another system
- `/api/v1/nodes/{code}` - find all systems containing a code
- `/api/v1/systems/stats` - leaf/total counts per system
- `/api/v1/equivalences/stats` - crosswalk statistics
- Auth endpoints: register, login, API key management

**MCP Server (20 tools, stdio transport):**
- list_systems, get_industry, browse_children, get_ancestors
- search_classifications, get_equivalences, translate_code, get_sector_overview
- translate_across_all_systems, compare_sector, find_by_keyword_all_systems
- get_crosswalk_coverage, get_system_diff, get_siblings, get_subtree_summary
- resolve_ambiguous_code, get_leaf_count, get_region_mapping
- describe_match_types, explore_industry_tree

**Auth system:**
- JWT-based auth (15-min tokens)
- API keys with `wot_` prefix, bcrypt-hashed, prefix-indexed
- Rate limits: anonymous 30 req/min, authenticated 1000 req/min

**Next.js frontend:**
- Home page with industry map and Galaxy View (D3 force simulation)
- System detail pages with sector view and crosswalk matrix
- Full-text explore/search page
- Node detail pages with breadcrumb, children panel, cross-system equivalences
- Dashboard with stats overview
- Dark/light theme support (next-themes)

**Infrastructure:**
- 277 tests (pytest, asyncpg, test_wot schema isolation)
- Neon PostgreSQL (serverless, pgbouncer compatible)
- robots.txt and llms.txt endpoints

### Database

- `classification_system` - 10 rows
- `classification_node` - 10,966 rows
- `equivalence` - 11,420 rows
- `app_user`, `api_key`, `usage_log` - auth tables

---

[Unreleased]: https://github.com/ramdhanyk/WorldOfTaxanomy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ramdhanyk/WorldOfTaxanomy/releases/tag/v0.1.0
