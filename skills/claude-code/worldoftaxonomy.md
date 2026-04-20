---
name: worldoftaxonomy
description: Classify businesses, products, occupations, diseases, or documents under global standard codes (NAICS, ISIC, NACE, HS, ICD, SOC, ISCO, CPC, UNSPSC, and 1000+ more). Translate codes between country/system versions. Find crosswalks, equivalents, hierarchies, siblings, ancestors, and structural comparisons across 1.2M nodes and 326K crosswalk edges. All 434 curated domain taxonomies are bridged to NAICS/ISIC/NACE via sector anchors; every edge carries an edge_kind label.
---

# WorldOfTaxonomy Skill

Use this skill when the user asks to classify something under a standard code, translate a code across systems (e.g. NAICS -> ISIC, ICD-10-CM -> ICD-10-GM, SOC -> ISCO), or explore the structure of any classification system.

## Access

Preferred: MCP server (exposes 24 tools).

Install on this machine:
```bash
# Claude Code (or Claude Desktop) config at ~/.claude.json or ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "worldoftaxonomy": {
      "command": "python",
      "args": ["-m", "world_of_taxonomy", "mcp"],
      "env": { "DATABASE_URL": "postgresql://..." }
    }
  }
}
```

Or use the hosted REST API directly at `https://worldoftaxonomy.com/api/v1` with header `Authorization: Bearer wot_<api_key>`. Get a key at `https://worldoftaxonomy.com/dashboard`.

## Key MCP tools (call directly when available)

- `classify_business(description)` - free-text -> taxonomy codes across all industry systems
- `search_classifications(query, system?)` - full-text search over node titles
- `translate_code(from_system, code, to_system)` - cross-system equivalent
- `translate_across_all_systems(from_system, code)` - fan out to every connected system
- `get_equivalences(system, code)` - all crosswalk edges for a code
- `get_industry(system, code)` - node detail
- `browse_children(system, code)` / `get_ancestors(...)` / `get_siblings(...)` - hierarchy walks
- `get_sector_overview(system, sector_code)` - top-level sector summary
- `get_crosswalk_coverage(from_system, to_system)` - how complete is a mapping
- `get_system_diff(system_a, system_b)` - structural comparison
- `explore_industry_tree(system)` - full tree walk with depth budget
- `list_classification_systems()` - discover available systems
- `list_crosswalks_by_kind(edge_kind, system_id?)` - counts + samples for one of {standard_standard, standard_domain, domain_standard, domain_domain}

## Key REST endpoints (fallback when MCP isn't installed)

```
GET /api/v1/systems                                    # list all 1000+ systems
GET /api/v1/systems/{id}                               # system detail + roots
GET /api/v1/systems/{id}/nodes/{code}                  # node detail
GET /api/v1/systems/{id}/nodes/{code}/children
GET /api/v1/systems/{id}/nodes/{code}/ancestors
GET /api/v1/systems/{id}/nodes/{code}/equivalences     # crosswalk edges
GET /api/v1/search?q=<term>&system=<optional>
POST /api/v1/classify     { "description": "..." }     # free-text classifier
GET /api/v1/equivalences/stats                         # crosswalk coverage matrix
```

## Domain taxonomies vs official standards

Every system carries a `category`: `"domain"` or `"standard"`. Domain systems (IDs start with `domain_`) are plain-language on-ramps curated by WorldOfTaxonomy. Standard systems are canonical codes (NAICS, ISIC, NACE, SIC, SOC, ICD, HS, etc). `classify_business` and `POST /classify` return `domain_matches` and `standard_matches` as separate arrays. Surface domain matches first - users recognize them instantly - then the standard codes for reporting. Every equivalence carries an `edge_kind` in {`standard_standard`, `standard_domain`, `domain_standard`, `domain_domain`}. Generated domain-bridge edges are `match_type='broad'`; filter `?edge_kind=standard_standard` (or `?match_type=exact`) to keep only authoritative statistical crosswalks. Details: https://worldoftaxonomy.com/guide/domain-vs-standard.

## When NOT to use

Don't invoke for generic "what is NAICS" explanations - answer from general knowledge. Invoke when the user wants a specific code, a translation, a mapping, or a structural query against live data.
