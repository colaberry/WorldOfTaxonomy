# Web Vocabularies

Web vocabularies are the type and concept systems used by AI assistants, search engines, and structured-data crawlers to label real-world entities on the public web. World Of Taxonomy hosts the type-tree subset of these vocabularies (the part that is enumerated and hierarchical, per the [Inclusion Policy](./inclusion-policy.md)). Property and relation vocabularies are out of scope.

## schema.org

| Field | Value |
|---|---|
| System ID | `schema_org` |
| Total types | 926 (rdfs:Class entries with the `schema:` prefix) |
| Authority | schema.org consortium (Google, Microsoft, Yahoo, Yandex) |
| License | CC BY-SA 3.0 |
| Source | https://schema.org/version/latest/schemaorg-current-https.jsonld |

schema.org publishes a vocabulary of types and properties that web pages and APIs use to mark up structured data so search engines and AI assistants can understand what a page is about. WoT ingests the type tree only:

- Rooted at `Thing`. Every type is a subclass of Thing (transitively).
- ~926 types organized via `rdfs:subClassOf` chains (CreativeWork, Person, Place, Action, etc.).
- ~57 types have multiple parents; WoT keeps the first listed parent as the canonical hierarchy edge and notes the alternative parents in the description.
- 100% description coverage native to the source (every class has `rdfs:comment`).

**Why this matters for AEO and SEO**: schema.org type tags are the single most important signal AI search overviews, ChatGPT browsing, and Google Knowledge Graph use to identify what a page is about. Hosting the full type tree in WoT means downstream products (WoO agent runtime, classification/crosswalk APIs) can cite schema.org URIs natively as the canonical anchor for "what kind of thing is this." It also enables crosswalks between schema.org types and domain classifications: `schema:Restaurant` to NAICS 7225, `schema:Hotel` to NAICS 7211, `schema:MedicalSpecialty` to MeSH, and so on.

**What WoT does not host**: the ~1,676 schema.org `rdf:Property` entries (`name`, `address`, `priceRange`, etc.) are property definitions, not classification categories. Per the inclusion policy, pure property vocabularies are out of scope. Consumers who need the full property surface should hit schema.org directly.

## Related vocabularies in WoT

| System | Codes | Role |
|---|---|---|
| `skos` | 17 | W3C Simple Knowledge Organization System (metamodel for thesauri) |
| `w3c_standards` | 16 | W3C standards index |
| `iab_content` | 21 | IAB Tech Lab content taxonomy for advertising |

These sit alongside schema.org as web-adjacent classification systems with smaller coverage than the schema.org type tree.

## What's not yet ingested

The following web-vocabulary candidates have been audited against the inclusion policy and are queued for follow-up PRs:

- **WordNet hypernym tree** (~82K synsets) - lexical semantic anchor.
- **DBpedia ontology** (~700 classes) - Wikipedia-derived class hierarchy.
- **SUMO / BFO / DOLCE** - upper ontologies (small, peripheral relevance).
- **FOAF classes**, **DCMI Type Vocabulary** - small auxiliary vocabularies.

The full Wikidata Q-number space (~100M entities) and the DBpedia instance set (~5M) are entity registries above WoT's size cap and out of scope. They belong in a sister product (a hypothetical "World of Registries" or directly inside WoO).

## How to use schema.org from WoT

```bash
# Look up a specific schema.org type
GET /api/v1/systems/schema_org/nodes/Restaurant

# Browse children of CreativeWork
GET /api/v1/systems/schema_org/nodes/CreativeWork/children

# Search across the type tree
GET /api/v1/search?q=medical&systems=schema_org

# Crosswalk to a domain classification (when wired)
GET /api/v1/systems/schema_org/nodes/Restaurant/equivalences
```

The MCP server exposes the same data via `get_industry`, `browse_children`, and `search_classifications` tools, so AI assistants can resolve a schema.org type to its WoT counterparts without leaving the chat.

## Related reading

- [Inclusion Policy](./inclusion-policy.md) - the four tests every WoT system must pass.
- [Crosswalk Map](./crosswalk-map.md) - how systems connect via equivalence edges.
- [Categories and Sectors](./categories-and-sectors.md) - how WoT organizes its catalog.
