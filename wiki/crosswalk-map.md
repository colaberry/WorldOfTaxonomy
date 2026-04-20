## Crosswalk Map - How Classification Systems Connect

> **TL;DR:** 326,000+ crosswalk edges link 1,000 classification systems through hub-and-spoke topology. ISIC is the industry hub, CPC bridges trade to industry, SOC/ISCO connect occupations, and every one of the 434 domain taxonomies is bridged to NAICS/ISIC/NACE via sector anchors. This guide maps the full topology and shows how to navigate translation paths.

---

## What is a crosswalk?

A crosswalk (or concordance) is a mapping between codes in two different classification systems. For example, NAICS 6211 ("Offices of Physicians") maps to ISIC 8620 ("Medical and dental practice activities").

Crosswalks have a match type that tells you how precise the mapping is:

| Type | Meaning | Example |
|------|---------|---------|
| `exact` | Identical scope and definition | NAICS 111110 "Soybean Farming" = ISIC 0111 |
| `partial` | Overlapping but not identical scope | NAICS 6211 partially overlaps ISIC 8620 |
| `broader` | Target has wider scope | A 6-digit NAICS to a 2-digit ISIC |
| `narrower` | Target has narrower scope | A section-level ISIC to a detailed NAICS |
| `related` | Conceptually related but structurally different | Domain taxonomy to parent NAICS sector |

## Core crosswalk topology

The knowledge graph has five major hubs. Each hub connects clusters of related systems.

```mermaid
graph TB
  subgraph Industry["Industry Hub"]
    ISIC["ISIC Rev 4\n766 codes"]
    NAICS["NAICS 2022\n2,125 codes"]
    NACE["NACE Rev 2\n996 codes"]
    NIC["NIC 2008\n2,070 codes"]
    ANZSIC["ANZSIC 2006\n825 codes"]
    SIC["SIC 1987\n1,176 codes"]
    GBT["GB/T 4754\n118 codes"]
    NAT80["80+ National\nISIC variants"]
  end
  subgraph Trade["Trade Hub"]
    CPC["CPC v2.1\n4,596 codes"]
    HS["HS 2022\n6,960 codes"]
    UNSPSC["UNSPSC v24\n77,337 codes"]
    HTS["HTS / CN / SITC"]
  end
  subgraph Occupation["Occupation Hub"]
    SOC["SOC 2018\n1,447 codes"]
    ISCO["ISCO-08\n619 codes"]
    ESCO["ESCO\n3,045 + 14,247"]
    ONET["O*NET-SOC\n867 codes"]
    CIP["CIP 2020\n2,848 codes"]
  end
  NAICS <-->|3,418 edges| ISIC
  ISIC <-->|1:1| NACE
  ISIC -.->|derived| NIC
  ISIC -.->|derived| ANZSIC
  ISIC -.->|derived| GBT
  ISIC -.->|derived| NAT80
  NAICS <-.->|legacy| SIC
  ISIC <-->|5,430 edges| CPC
  CPC <-->|11,686 edges| HS
  CPC -.-> UNSPSC
  HS -.-> HTS
  SOC <-->|992 edges| ISCO
  ISCO <-->|6,048 edges| ESCO
  SOC <-->|1,734 edges| ONET
  CIP -->|5,903 edges| SOC
  ISCO <-->|44 edges| ISIC
```

## Industry classification hub

ISIC Rev 4 is the central node for industry classification. Every major national system connects through it.

```mermaid
graph LR
  NAICS["NAICS 2022"] <-->|3,418| ISIC["ISIC Rev 4"]
  ISIC <-->|1:1| NACE["NACE Rev 2"]
  NACE -->|1:1| WZ["WZ 2008\nGermany"]
  NACE -->|1:1| NAF["NAF Rev 2\nFrance"]
  NACE -->|1:1| ATECO["ATECO 2007\nItaly"]
  NACE -->|1:1| MORE["30+ more\nEU variants"]
  ISIC -->|derived| NIC["NIC 2008\nIndia"]
  ISIC -->|derived| ANZSIC["ANZSIC 2006\nAU/NZ"]
  ISIC -->|derived| GBT["GB/T 4754\nChina"]
  ISIC -->|adapted| NAT80["80+ national\nadaptations"]
```

NACE national variants (WZ, NAF, ATECO, PKD, SBI, SNI, etc.) share the identical 996-code structure. Each has a 1:1 mapping to NACE Rev 2 and transitively to ISIC Rev 4.

## Product and trade hub

CPC v2.1 is the bridge between trade codes and industry codes.

```mermaid
graph LR
  HS["HS 2022\n6,960 codes"] <-->|11,686 edges| CPC["CPC v2.1\n4,596 codes"]
  CPC <-->|5,430 edges| ISIC["ISIC Rev 4"]
  HS -->|extended| HTS["HTS (US)"]
  HS -->|extended| CN["CN 2024 (EU)"]
  HS -->|extended| AHTN["ASEAN Tariff"]
  HS -->|extended| NCM["MERCOSUR Tariff"]
  HS -.->|aggregated| SITC["SITC Rev 4\n77 codes"]
  HS -.->|aggregated| BEC["BEC Rev 5\n29 codes"]
  CPC -.-> UNSPSC["UNSPSC v24\n77,337 codes"]
```

This means you can trace a trade code (HS) to its product category (CPC) to the industry that produces it (ISIC/NAICS).

## Occupation and education hub

SOC 2018 and ISCO-08 are the twin hubs for occupation data.

```mermaid
graph LR
  CIP["CIP 2020\n2,848 programs"] -->|5,903 edges| SOC["SOC 2018\n1,447 occupations"]
  CIP -->|1,615 edges| ISCEDF["ISCED-F 2013\n122 fields"]
  SOC <-->|992 edges| ISCO["ISCO-08\n619 occupations"]
  ISCO <-->|6,048 edges| ESCO["ESCO Occupations\n3,045"]
  SOC <-->|1,734 edges| ONET["O*NET-SOC\n867"]
  ISCO -->|44 edges| ISIC["ISIC Rev 4"]
  SOC -.-> NAICS["NAICS 2022"]
```

CIP 2020 (educational programs) connects to SOC (occupations) with 5,903 edges - the education-to-career pipeline.

## Geographic and domain hubs

```mermaid
graph TB
  subgraph Geo["Geographic"]
    ISO1["ISO 3166-1\n271 countries"]
    ISO2["ISO 3166-2\n5,246 subdivisions"]
    UNM["UN M.49\n272 regions"]
  end
  subgraph Domain["Domain Crosswalks"]
    N484["NAICS 484\nTruck Transportation"]
    N11["NAICS 11\nAgriculture"]
    N21["NAICS 21\nMining"]
    N22["NAICS 22\nUtilities"]
    N23["NAICS 23\nConstruction"]
  end
  ISO1 <--> ISO2
  ISO1 <--> UNM
  N484 -->|~200 edges| TRUCK["Truck domain\n7 vocabularies"]
  N11 -->|~48 edges| AG["Agriculture domain\n11 vocabularies"]
  N21 -->|~31 edges| MINE["Mining domain\n6 vocabularies"]
  N22 -->|~20 edges| UTIL["Utility domain\n6 vocabularies"]
  N23 -->|~27 edges| CONST["Construction domain\n6 vocabularies"]
```

Each domain taxonomy links back to its parent NAICS sector, creating drill-down paths from broad industry codes to specialized vocabularies.

As of the sector-anchor pass, all 434 domain taxonomies (up from the 15 original pilots shown above) carry at least one bridge edge to NAICS 2022, plus parallel fan-out edges into ISIC Rev 4 and NACE Rev 2 where the NAICS anchor has an existing international crosswalk. Generated edges are stamped `match_type='broad'` and one of two provenance values:

| Provenance | What it means |
|------------|---------------|
| `derived:sector_anchor:v1` | Direct NAICS<->domain bridge written by `crosswalk_domain_anchors.py` |
| `derived:sector_anchor:v1:fanout` | ISIC<->domain or NACE<->domain edge derived via a NAICS<->ISIC (or NACE) self-join |

Filter `?match_type=exact` if you want to exclude every generated bridge and see only authoritative exact statistical concordances.

## The four edge kinds

Every equivalence response now carries an `edge_kind` computed from the categories of both endpoints. See [domain-vs-standard](domain-vs-standard.md) for the full pattern. Quick reference:

| `edge_kind`         | Description |
|---------------------|-------------|
| `standard_standard` | Pre-existing statistical crosswalks (NAICS<->ISIC, ISIC<->NACE, HS<->CPC, SOC<->ISCO, ...) |
| `standard_domain`   | Bridge from an official code to a curated domain taxonomy |
| `domain_standard`   | Bridge from a domain taxonomy back to an official code |
| `domain_domain`     | Reserved for future cross-domain edges; none generated yet |

Use the filter on any equivalence or translation endpoint:

```
GET /api/v1/systems/naics_2022/nodes/6211/equivalences?edge_kind=standard_standard
GET /api/v1/systems/naics_2022/nodes/6211/equivalences?edge_kind=standard_domain,domain_standard
```

Stats grouped by edge kind:

```bash
curl "https://worldoftaxonomy.com/api/v1/equivalences/stats?group_by=edge_kind"
```

## Translation paths

Not all systems have direct crosswalks. You translate between systems by following a path through intermediate hubs.

### Example: German industry code to US occupation

```mermaid
graph LR
  WZ["WZ 2008\nGerman industry"] -->|1:1| NACE["NACE Rev 2"]
  NACE -->|1:1| ISIC["ISIC Rev 4"]
  ISIC -->|44 edges| ISCO["ISCO-08"]
  ISCO -->|992 edges| SOC["SOC 2018\nUS occupation"]
```

### Example: HS trade code to NAICS industry

```mermaid
graph LR
  HS["HS 2022\ntrade code"] -->|11,686| CPC["CPC v2.1"]
  CPC -->|5,430| ISIC["ISIC Rev 4"]
  ISIC -->|3,418| NAICS["NAICS 2022"]
```

## API for crosswalk navigation

### Direct equivalences

```bash
# Get all systems that NAICS 6211 maps to
curl https://worldoftaxonomy.com/api/v1/systems/naics_2022/nodes/6211/equivalences

# Translate to all connected systems at once
curl https://worldoftaxonomy.com/api/v1/systems/naics_2022/nodes/6211/translations
```

### Crosswalk statistics

```bash
# Overall crosswalk stats
curl https://worldoftaxonomy.com/api/v1/equivalences/stats

# Stats for a specific system
curl "https://worldoftaxonomy.com/api/v1/equivalences/stats?system_id=naics_2022"
```

### Compare systems

```bash
# Side-by-side top-level comparison
curl "https://worldoftaxonomy.com/api/v1/compare?a=naics_2022&b=isic_rev4"

# Codes in system A with no mapping to B
curl "https://worldoftaxonomy.com/api/v1/diff?a=naics_2022&b=isic_rev4"
```

## MCP tools for crosswalks

| Tool | Purpose |
|------|---------|
| `get_equivalences` | Direct crosswalk mappings for a code |
| `translate_code` | Translate a code to a specific target system |
| `translate_across_all_systems` | Translate to all connected systems |
| `get_crosswalk_coverage` | Coverage statistics for a crosswalk pair |
| `get_system_diff` | Codes with no mapping between two systems |
| `compare_sector` | Side-by-side sector comparison |
| `describe_match_types` | Explain the match type categories |
| `list_crosswalks_by_kind` | Counts + samples for a specific `edge_kind` (standard_standard, standard_domain, domain_standard, domain_domain); optionally narrow to a single system |
