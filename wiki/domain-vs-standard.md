# Domain Taxonomies vs Official Standards

WorldOfTaxonomy ships two complementary kinds of classification system, and every public surface (web app, REST API, MCP server) now labels them explicitly so downstream consumers can treat them differently.

## The two categories

| Category | `category` value | System ID pattern | Examples | Role |
|----------|------------------|-------------------|----------|------|
| Domain taxonomy | `domain` | IDs start with `domain_` | `domain_truck_freight`, `domain_ai_deployment`, `domain_fintech_service` | Plain-language on-ramps curated by WorldOfTaxonomy. Shorter (15-50 nodes), written in working-industry vocabulary, and crosswalked into the relevant official standard. |
| Official standard | `standard` | Everything else | `naics_2022`, `isic_rev4`, `nace_rev2`, `soc_2018`, `icd10_cm`, `hs_2022` | Published by a government, intergovernmental body, or standards authority. These are the codes auditors, statistical agencies, and regulators require. |

The split is a pure function of `system_id`: if the ID starts with `domain_`, it is a domain taxonomy; otherwise it is an official standard. The Python helper `world_of_taxonomy.category.get_category()` and the TypeScript helper `frontend/src/lib/category.ts` are the two sources of truth and stay in sync.

## Why the split exists

Users describing a business in plain language ("telemedicine platform", "frozen-goods logistics", "AI inference startup") rarely know the NAICS code by heart. They read domain-taxonomy labels like "Telemedicine Modality Types" or "Cold Chain Types" much faster than five-digit NAICS numbers.

Domain taxonomies are therefore the front door: surface them first, let the user recognize their own business, then fan out through crosswalk edges into the matching NAICS, ISIC, NACE, SIC, or SOC codes that an accountant or statistical agency will accept.

## How each surface reflects the split

### Web app

- `/classify` shows two sections in order: "Start here: Domain taxonomies" followed by "Official standard codes". If only one category has matches, the heading is dropped and cards render as a flat list.
- `/system/{id}` shows a badge next to the system name: "Domain taxonomy" or "Official standard".
- `/system/{id}/node/{code}` splits cross-system equivalences into "Domain taxonomies" and "Official standards" sub-sections when both are present.

### REST API

- `GET /api/v1/systems` and `GET /api/v1/systems/{id}` return a `category` field (`"domain"` or `"standard"`).
- `GET /api/v1/systems?category=domain` (or `?category=standard`) filters the list.
- `POST /api/v1/classify/demo` returns `domain_matches` and `standard_matches` arrays instead of a single flat `matches` array. Each match carries its own `category` field. For compound inputs, each atom also has `domain_matches` and `standard_matches`.
- Every node returned by the API carries a `category` field derived from its parent system.

### MCP server

- The `classify_business` tool returns `domain_matches` and `standard_matches` (plus `domain_matches` and `standard_matches` per atom for compound inputs).
- `list_classification_systems`, `search_classifications`, and `get_industry` stamp each node/system with a `category` field.

## Consuming the split

If you are building on top of WorldOfTaxonomy:

1. **Route users through domain taxonomies first** when the input is free text. They are written for humans.
2. **Fall back to official standards** when the user asks for a statistical code, needs to report to a government agency, or wants cross-country comparability.
3. **Use crosswalks** (`GET /api/v1/systems/{id}/nodes/{code}/equivalences`) to hop from a domain match to the official standard code. The domain taxonomies are pre-wired with equivalence edges into NAICS, ISIC, or other relevant standards.
4. **Never mix the two in a single ranked list** without signaling the category - users cannot tell at a glance that `domain_truck_freight` and `naics_2022` play different roles.

## Example

A request for "last-mile delivery for frozen groceries" returns:

- Domain matches: `domain_last_mile_delivery`, `domain_cold_chain`, `domain_freight_class`
- Standard matches: `naics_2022: 492110` (Couriers and Express Delivery Services), `isic_rev4: 5320` (Postal and courier activities)

The domain matches are recognizable instantly. The standard matches are what the user needs to give to their accountant.

## How the bridge works

Every one of the 434 domain taxonomies is wired to at least one NAICS 2022 anchor code. This means there is no such thing as a domain island: if a user's query surfaces a `domain_*` match, there is always a bridge edge to a standard reporting code right next to it.

The bridges are built in two passes:

1. **Sector-anchor generator.** A single mapping table (`world_of_taxonomy/ingest/domain_anchors.json`) maps every `domain_*` system to one to three NAICS 2022 sector anchors. The generator emits a bidirectional `equivalence` edge between each anchor and each level-1 code of the domain taxonomy, stamped with `match_type='broad'` and provenance `derived:sector_anchor:v1`.
2. **ISIC / NACE fan-out.** For every new NAICS->domain edge, a single self-join against the existing NAICS<->ISIC and NAICS<->NACE crosswalks produces parallel edges so European and UN users reach the same domain taxonomies through their native standards. These carry provenance `derived:sector_anchor:v1:fanout`.

Because `match_type` on every generated edge is `broad`, consumers can filter them out if they need exact-match statistical crosswalks only (the pre-existing NAICS<->ISIC / NAICS<->NACE exact edges are untouched).

## The four edge kinds

Every equivalence response now carries an `edge_kind` computed from whether each endpoint is a domain taxonomy (`system_id` starts with `domain_`) or an official standard:

| `edge_kind`         | Source   | Target   | Meaning |
|---------------------|----------|----------|---------|
| `standard_standard` | standard | standard | Classic statistical crosswalk (e.g. NAICS 6211 <-> ISIC 8620) |
| `standard_domain`   | standard | domain   | Official code bridging into a curated domain taxonomy (e.g. NAICS 6212 -> `domain_dental`) |
| `domain_standard`   | domain   | standard | The reverse: domain taxonomy bridging back to an official code |
| `domain_domain`     | domain   | domain   | Reserved for future cross-domain edges; not yet generated |

Filter on `edge_kind` to scope the graph exactly:

```
GET /api/v1/systems/naics_2022/nodes/6211/equivalences?edge_kind=standard_standard
GET /api/v1/systems/naics_2022/nodes/6211/equivalences?edge_kind=standard_domain,domain_standard
```

The MCP tool `list_crosswalks_by_kind` wraps the same filter for agents:

```
list_crosswalks_by_kind(edge_kind="standard_domain", system_id="naics_2022")
```

`source_category` and `target_category` are also returned alongside `edge_kind` so lazy consumers can filter without parsing the composite label.
