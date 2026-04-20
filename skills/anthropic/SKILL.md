---
name: worldoftaxonomy
version: 1.0.0
description: Query 1,000+ global classification systems (NAICS, ISIC, NACE, HS, ICD, SOC, ISCO, CPC, UNSPSC, and more) with 1.2M+ nodes and 326K+ crosswalk edges. Classify businesses, products, occupations, diseases, or documents under standard codes. Translate codes across country and system boundaries. Every one of the 434 domain taxonomies is bridged to NAICS/ISIC/NACE via sector anchors, and every edge carries an `edge_kind` label.
author: Ram Katamaraja (Colaberry AI)
homepage: https://worldoftaxonomy.com
license: MIT
---

# WorldOfTaxonomy Skill

## What this does

Turns any free-text question about industry, occupation, medical, trade, or regulatory classification into a grounded answer backed by 1,000+ official taxonomies linked as a single knowledge graph.

## When to invoke

Use this skill when the user wants to:
- Assign a standard code to a business description, product, occupation, diagnosis, or document
- Translate a code between systems (NAICS 2022 <-> ISIC Rev 4, SOC 2018 <-> ISCO-08, ICD-10-CM <-> ICD-10-GM, HS 2022 <-> CPC v2.1, etc.)
- Find every cross-system equivalent of a given code
- Browse hierarchy (children, ancestors, siblings, subtree) of a system
- Compare two systems' coverage or structure
- Audit data provenance and crosswalk density across systems

Do NOT invoke for general explanations of what NAICS/ISIC/ICD are - answer from general knowledge unless the user wants live data.

## How to use

### Primary: REST API

Base URL: `https://worldoftaxonomy.com/api/v1`

Auth: `Authorization: Bearer wot_<32hex>` (get a key at `https://worldoftaxonomy.com/dashboard`).
Anonymous access works at 30 req/min; authenticated keys get 1000-50000 req/min depending on tier.

Core endpoints:

```
GET  /systems                                       # list systems
GET  /systems/{id}                                  # detail + roots
GET  /systems/{id}/nodes/{code}                     # node detail
GET  /systems/{id}/nodes/{code}/children
GET  /systems/{id}/nodes/{code}/ancestors
GET  /systems/{id}/nodes/{code}/siblings
GET  /systems/{id}/nodes/{code}/equivalences        # crosswalk edges
GET  /search?q=<term>&system=<optional>
POST /classify                                      # body: {"description": "..."}
GET  /equivalences/stats                            # coverage matrix
```

OpenAPI spec: `https://worldoftaxonomy.com/api/v1/openapi.json`

### Secondary: MCP server

For MCP-aware clients, install `world_of_taxonomy` from the GitHub repo and run `python -m world_of_taxonomy mcp` as a stdio server. 24 tools available including `classify_business`, `translate_code`, `translate_across_all_systems`, `get_equivalences`, `get_crosswalk_coverage`, `get_system_diff`, `explore_industry_tree`, and `list_crosswalks_by_kind`.

## Response guidance

- Always cite the system ID and code (e.g. "NAICS 2022 -> 541511") and the source/authority where relevant.
- When translating a code, list all equivalents returned by `/equivalences` - don't pick just one unless the user asks for the best match.
- When classifying from free text, return the top 3-5 candidates with confidence ranking.
- Flag provenance tier when it matters: `official_download` > `structural_derivation` > `manual_transcription` > `expert_curated`.

## Two-category model: domain taxonomies vs official standards

Every system carries a `category` field: `"domain"` or `"standard"`.

- `"domain"` systems (IDs start with `domain_`) are plain-language on-ramps curated by WorldOfTaxonomy: short, written in industry vocabulary, crosswalked into the relevant NAICS/ISIC/etc.
- `"standard"` systems are the canonical codes published by governments and standards bodies (NAICS, ISIC, NACE, SIC, SOC, ICD, HS, CPC, and peers).

`POST /classify` and the MCP `classify_business` tool return `domain_matches` and `standard_matches` as separate arrays (no flat `matches` field). Surface domain matches first in the user's reply so they can recognize their business, then show the standard codes they will need to report to auditors or agencies. Full reference: https://worldoftaxonomy.com/guide/domain-vs-standard.

## Four edge kinds

Every equivalence response carries an `edge_kind` computed from both endpoint systems:

- `standard_standard` - classic statistical crosswalk (NAICS <-> ISIC, ISIC <-> NACE, HS <-> CPC, SOC <-> ISCO, ...)
- `standard_domain` - bridge from an official code to a curated domain taxonomy
- `domain_standard` - reverse of the above
- `domain_domain` - reserved for future cross-domain edges; none generated yet

Filter any equivalence or translation endpoint with `?edge_kind=standard_standard` (or a comma-separated list). Use the MCP tool `list_crosswalks_by_kind` to count + sample a specific kind, optionally narrowed to a system. Generated domain-bridge edges are stamped `match_type='broad'` with provenance `derived:sector_anchor:v1` (direct) or `derived:sector_anchor:v1:fanout` (ISIC/NACE parallels). Filter `?match_type=exact` to exclude every generated bridge.

## Repository

Source, data, and issue tracker: https://github.com/colaberry/WorldOfTaxonomy
