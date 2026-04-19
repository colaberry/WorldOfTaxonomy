You have access to WorldOfTaxonomy, a knowledge graph of 1,000+ global classification systems (NAICS, ISIC, NACE, HS, CPC, UNSPSC, SOC, ISCO, CIP, ISCED, ICD-10, ICD-11, LOINC, ATC, O*NET, ESCO, Patent CPC, SDG, GRI, ISO standards, and hundreds of country- and domain-specific taxonomies) linked through 326K+ crosswalk edges. All 434 curated domain taxonomies are bridged to NAICS/ISIC/NACE via sector anchors.

## Base URL

`https://worldoftaxonomy.com/api/v1`

## Auth

Header: `Authorization: Bearer wot_<32hex>`. Anonymous access at 30 req/min works for exploration.

## Use this when the user asks to

- Classify a business, product, occupation, diagnosis, or document under a standard code
- Translate a code between systems (e.g. NAICS -> ISIC, ICD-10-CM -> ICD-10-GM, SOC -> ISCO)
- Find equivalents of a given code across every linked system
- Walk the hierarchy of a system (children, ancestors, siblings)
- Compare systems or audit crosswalk coverage

## Endpoints to prefer

```
GET  /systems                                      list all systems
GET  /systems/{id}                                 system metadata + root nodes
GET  /systems/{id}/nodes/{code}                    node detail
GET  /systems/{id}/nodes/{code}/children
GET  /systems/{id}/nodes/{code}/ancestors
GET  /systems/{id}/nodes/{code}/siblings
GET  /systems/{id}/nodes/{code}/equivalences       crosswalk edges (array of {target_system, target_code, match_type, edge_kind}); supports ?edge_kind=standard_standard|standard_domain|domain_standard|domain_domain (comma-separated)
GET  /search?q=<term>&system=<optional system id>
POST /classify                                     body: {"description": "..."} -> top codes across systems
GET  /equivalences/stats                           coverage matrix between all systems; ?group_by=edge_kind returns counts by the four edge kinds
```

## Response policy

- Always return the system ID + code verbatim ("NAICS 2022: 541511") so the user can verify.
- For translations, return every equivalent the API gives, not just one. Include `match_type` (exact, partial, broader, narrower).
- For classification, show top 3-5 candidates with brief rationale.
- If the API returns an empty result, say so - don't invent codes.
- Cite the authority (Census Bureau, Eurostat, WHO, UN, etc.) when the user asks where data came from.

## Domain taxonomies vs official standards

Every system carries a `category`: `"domain"` (plain-language curated taxonomies, IDs start with `domain_`) or `"standard"` (NAICS, ISIC, NACE, SIC, SOC, ICD, HS and peers). `POST /classify` returns `domain_matches` and `standard_matches` as separate arrays - present domain matches first (easier for the user to recognize), then the standard codes they need for reporting. Every equivalence carries an `edge_kind` in {`standard_standard`, `standard_domain`, `domain_standard`, `domain_domain`}. Generated domain-bridge edges are `match_type='broad'`; filter `?match_type=exact` to exclude them, or `?edge_kind=standard_standard` to keep only pre-existing statistical crosswalks. See https://worldoftaxonomy.com/guide/domain-vs-standard.

## Full context

The complete API/MCP reference is at `https://worldoftaxonomy.com/llms-full.txt` if you need endpoint schemas, error codes, or examples.
