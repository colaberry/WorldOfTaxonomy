# Inclusion Policy

World Of Taxonomy is a unified knowledge graph of **published classification, coding, and reference systems** that humans and machines use to label, group, or reference real-world things. Its job is to make these systems individually discoverable and collectively interoperable through crosswalks.

This page is the policy that governs which systems get added to WoT. It exists so contributors, downstream portfolio products (WoO, WoUC, WoA), and AI assistants doing research against the graph can answer "should this artifact be in WoT?" without guessing.

## What qualifies for inclusion

A system fits in WoT if it satisfies all four:

1. **Published and externally maintained.** It has a named publisher, a standards body, government agency, scientific community, or recognized industry consortium, and is referenced by some user community outside WoT itself. Internal or proprietary lists do not qualify.

2. **Stable identifiers.** Each entry has a code, key, URI, or other stable identifier that callers cite by reference (`NAICS 5417`, `ICD-10-CM E11.9`, `schema.org/Article`, `FIBO Equity`). Identifiers are assigned by the publisher, not minted by WoT. The one historical exception is the `domain_*` taxonomies, which are WoT-curated plain-language on-ramps; new systems are expected to use external identifiers.

3. **Enumerated or hierarchical structure.** Either a finite list (HTTP status codes, blood types, SPDX licenses) or a tree of categories (NAICS sectors, ICD chapters, schema.org type tree). Open-ended relational graphs without inherent hierarchy, e.g. a triple store of arbitrary semantic relations, do not qualify.

4. **Practical size.** Soft cap of about 500,000 nodes per system. Larger systems may still be admitted as a documented subset (top-N hierarchical levels, the publisher's official "major" or "core" subset, a stable extract anchored to a specific revision) with the truncation explicitly noted in the system's metadata.

## What does not qualify

- **Live operational data.** Customer rosters, vendor catalogs, asset registers, transaction logs, anything that grows through ongoing business activity. WoT is reference data, not application state.
- **Lists of individual persons.** Even if published, person-level rosters are out of scope.
- **Pure property or relation vocabularies.** Vocabularies that define predicates without a meaningful enumerated value space (FOAF `foaf:knows`, Dublin Core `dc:creator`). The *class hierarchy* of such a vocabulary may qualify on its own; its property definitions alone do not.
- **Entity registries above the size cap.** Wikidata's 100M Q-numbers, DBpedia's 5M instances, GeoNames' 12M places. Documented subtrees of these (NCBI Taxonomy from Wikidata, GeoNames feature codes, the schema.org type tree) may qualify on their own merits and should be ingested as their own WoT systems with the publisher's identifiers preserved.

## Crosswalks are valuable but not required

A system does not need to crosswalk to anything else to be included. Many existing WoT systems are deliberately isolated reference scales: Mohs hardness, Apgar score, Beaufort wind, HTTP status codes, SPDX licenses, Unicode emoji categories, blood types. Crosswalks compound a system's utility but are an output of inclusion, not a precondition.

When a system does have natural crosswalk surface to existing WoT content, that should be wired up in the same PR as the ingester.

## When in doubt

Default to **inclusion** if the system is published, identifier-bearing, and within the size cap. WoT's value scales with breadth. The failure mode of over-inclusion is a slightly cluttered catalog. The failure mode of under-inclusion is a contributor or downstream portfolio product needing to maintain a parallel store of what WoT should already have.

## Versioning and revisions

When a system publishes a new revision (NAICS 2017 to 2022, ICD-10 to ICD-11), both versions remain in WoT as distinct systems. Crosswalks between revisions are first-class equivalences, not implicit "latest wins" upgrades. This protects downstream consumers who must keep using the older revision for regulatory or contractual reasons.

## What this policy does not do

This policy does not retire or deprecate any existing system. The current catalog is what it is, and the policy applies prospectively to new additions and to deciding whether suggested additions belong. Where an existing entry sits awkwardly against the policy (a shallow skeleton, an internally-minted ID), that is treated as a quality-improvement opportunity, not a removal trigger.

## Related reading

- [Domain Taxonomies vs Official Standards](./domain-vs-standard.md) for the split between WoT-curated plain-language on-ramps and external standards.
- [Data Quality and Provenance](./data-quality.md) for the four-tier provenance framework that every ingested system is graded against.
- [Categories and Sectors](./categories-and-sectors.md) for the 16 categories used to organize the catalog.
