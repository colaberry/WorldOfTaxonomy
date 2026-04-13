# Changelog

All notable changes to WorldOfTaxanomy are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

**World Map visualization (home page):**
- Interactive D3 `geoNaturalEarth1` choropleth world map as the top section of the home page
- Color-coded by taxonomy coverage depth: green = official national standard, blue = regional/UN coverage, grey = UN recommended only
- Hover tooltips showing system count, official standard status, sector strength count per country
- Click navigates to `/country/{code}` country profile page
- `GET /api/v1/countries/stats` bulk endpoint powering the world map (per-country aggregate stats)
- `WorldMap.tsx` component in `frontend/src/components/visualizations/`

**Country Taxonomy Profile feature:**
- New `country_system_link` DB table mapping ISO 3166-1 alpha-2 codes to applicable classification systems with relevance values (`official` | `regional` | `recommended` | `historical`)
- `crosswalk_country_system` ingester with ~310 entries covering all 249 countries
- `GET /api/v1/countries/{code}` REST endpoint - full taxonomy profile (systems + sector strengths)
- `GET /api/v1/countries/stats` REST endpoint - bulk stats for world map
- `GET /api/v1/systems?country={code}` query param on systems endpoint
- `get_country_taxonomy_profile` MCP tool (21st tool) - country code -> systems + sector strengths
- `get_systems_for_country()` and `get_country_sector_strengths()` query functions

**ICD-11 MMS from WHO SimpleTabulation ZIP:**
- New `ingest_icd_11_from_zip()` function supporting `SimpleTabulation-ICD-11-MMS-en.zip`
- 37,052 nodes: 28 chapters + 1,360 block groupings + 35,664 diagnostic categories (up from ~14,223 via parquet)
- Full parent-child hierarchy resolved via Foundation URI lookup (0 orphans)
- Auto-selected when `data/SimpleTabulation-ICD-11-MMS-en.zip` present (ZIP > parquet > CSV priority)

**Magna Compass 2026 R2 - Gap Closure (16 new domain taxonomies):**

*CORE pillar gaps:*
- Chemical Industry Types (`domain_chemical_type`, 29 nodes: petrochemicals, specialty chemicals, polymers, industrial gases, etc.)
- Defence and Security Types (`domain_defence_type`, 23 nodes: land/naval/air/space systems, cyber, intelligence, logistics)
- Water and Environment Types (`domain_water_env`, 28 nodes: treatment, distribution, wastewater, desalination, remediation)

*EMERGING pillar - all 12 sectors now have structured domain vocabularies:*
- AI and Data Types (`domain_ai_data`, 25 nodes: foundation models, generative AI, data infrastructure, AI verticals, MLOps)
- Biotechnology and Genomics (`domain_biotech`, 26 nodes: drug discovery, genomics, cell/gene therapy, biomanufacturing)
- Space and Satellite Economy (`domain_space`, 24 nodes: launch vehicles, satellite types, earth observation, ground segment)
- Climate Technology (`domain_climate_tech`, 30 nodes: solar, wind, green hydrogen, CCUS, EVs, carbon markets)
- Advanced Materials (`domain_adv_materials`, 27 nodes: composites, biomaterials, nanomaterials, smart materials)
- Quantum Computing (`domain_quantum`, 23 nodes: superconducting, trapped ion, photonic qubits, error correction, sensing)
- Digital Assets and Web3 (`domain_digital_assets`, 25 nodes: Layer 1/2, DeFi, NFTs, stablecoins, CBDC, custody)
- Autonomous Systems and Robotics (`domain_robotics`, 27 nodes: industrial, collaborative, AMR, drones, humanoid, surgical)
- New Energy Storage (`domain_energy_storage`, 25 nodes: Li-ion, solid-state, flow batteries, grid-scale, hydrogen storage)
- Next-Generation Semiconductors (`domain_semiconductor`, 31 nodes: logic, memory, power, photonics, MEMS, WBG, packaging)
- Synthetic Biology (`domain_synbio`, 28 nodes: metabolic engineering, CRISPR, cell-free, cultured meat, biosensors)
- Extended Reality and Metaverse (`domain_xr_meta`, 27 nodes: VR, AR, MR, spatial computing, haptics, metaverse platforms)

*Geographic synergy crosswalk:*
- Nation-Sector Geographic Synergy Crosswalk (`crosswalk_geo_sector`, 98 edges: ISO 3166-1 countries -> NAICS 2-digit sectors, leadership/emerging strength)

**Phase 9 - Truck Transportation Domain Deep-Dives (prototype for all industries):**
- Truck Freight Types (`domain_truck_freight`, 44 nodes: mode, equipment, service level, cargo type)
- Truck Vehicle Classes (`domain_truck_vehicle`, 23 nodes: DOT GVWR Classes 1-8 + 13 body types)
- Truck Cargo Classification (`domain_truck_cargo`, 46 nodes: commodity groups, DOT hazmat classes 1-9, handling, regulatory)
- FMCSA -> Truck Domain crosswalk (`crosswalk_fmcsa_truck`, ~50 edges: HOS, ELD, CDL, HAZMAT, VIM, FR, OA, CSF, AR)
- Truck Carrier Operations (`domain_truck_ops`, 27 nodes: carrier type, fleet size, business model, route pattern)
- NAICS 484 -> Truck Domain crosswalk (`crosswalk_naics484_domains`, ~200 edges linking NAICS 484xxx to all 4 domain taxonomies)

**Phase 8 - Regulatory and Compliance Classification:**
- CFR Title 49 Transportation (`cfr_title_49`, 104 nodes: Parts 171-173, 177, 382, 383, 387, 390-397)
- FMCSA Regulations (`fmcsa_regs`, 80 nodes: HOS, ELD, CDL, DAT, VIM, HAZMAT, FR, OA, CSF, AR)
- CFR / NAICS crosswalk (`crosswalk_cfr_naics`, ~300 edges: CFR Title 49 parts -> NAICS 484/485/492)
- GDPR Articles (`gdpr_articles`, 110 nodes: 11 chapters + 99 articles with full titles)
- ISO 31000 Risk Framework (`iso_31000`, 47 nodes: Clauses 4-10 + Annex A)

**Phase 7 - Skills and Knowledge:**
- ESCO Occupations (`esco_occupations`, ~2,942 nodes: European occupational classification)
- ESCO Skills (`esco_skills`, ~13,890 nodes: European skills and competences taxonomy)
- ESCO / ISCO-08 crosswalk (`crosswalk_esco_isco`, ~2,942 bidirectional edges)
- O*NET-SOC (`onet_soc`, ~867 nodes: US occupational information network, base occupations)
- O*NET / SOC 2018 crosswalk (`crosswalk_onet_soc`, ~867 exact-match edges)
- Patent CPC (`patent_cpc`, ~260,000 nodes: 9 sections A-H, Y; 5-level hierarchy)

**Phase 6 - Financial and Environmental:**
- COFOG (`cofog`, 188 nodes: 10 divisions, 69 groups, 109 classes)
- GICS Bridge (`gics_bridge`, 11 nodes: 11 public sector names only, no proprietary data)
- GHG Protocol (`ghg_protocol`, 20 nodes: Scope 1/2/3 categories)

**Phase 5 - Health and Clinical:**
- ATC WHO Drug Classification (`atc_who`, 6,440 nodes: 14 anatomical groups, 5 levels)
- ICD-11 MMS ingester (requires manual download from icd.who.int)
- LOINC ingester (requires manual download from loinc.org)

**Phase 4 - Education:**
- ISCED-F 2013 Fields of Study (`iscedf_2013`, 122 nodes: 11 broad + 29 narrow + 82 detailed fields)
- CIP 2020 Classification of Instructional Programs (`cip_2020`, 2,848 nodes: 47 2-digit, 397 4-digit, 2,404 6-digit)
- CIP 2020 / SOC 2018 crosswalk (`crosswalk_cip_soc`, ~2,000 bidirectional edges)
- CIP 2020 / ISCED-F crosswalk (`crosswalk_cip_iscedf`, ~122 bidirectional edges)

**Phase 3 - Occupational Classification:**
- SOC 2018 (`soc_2018`, 1,447 nodes: 23 major groups, 98 minor, 459 broad, 867 detailed)
- ISCO-08 (`isco_08`, 619 nodes: 10 major, 43 sub-major, 130 minor, 436 unit groups)
- SOC 2018 / ISCO-08 crosswalk (`crosswalk_soc_isco`, 1,984 bidirectional edges)

**Phase 2 - Product and Trade Classification:**
- HS 2022 Harmonized System (`hs_2022`, 6,960 nodes: 21 sections, 97 chapters, 1,229 headings, 5,613 subheadings)
- HS 2022 / ISIC Rev 4 crosswalk (`crosswalk_hs_isic`, ~3,010 edges, broad)
- CPC v2.1 Central Product Classification (`cpc_v21`, 4,596 nodes: 10 sections, 71 divisions, 329 groups, 1,299 classes, 2,887 subclasses)
- CPC v2.1 / ISIC Rev 4 crosswalk (`crosswalk_cpc_isic`, ~5,430 bidirectional edges)
- HS 2022 / CPC v2.1 crosswalk (`crosswalk_cpc_hs`, ~11,686 bidirectional edges)
- UNSPSC v24 (`unspsc_v24`, 77,337 nodes: 57 segments, 465 families, 5,313 classes, 71,502 commodities)

**Phase 1 - Geographic Foundation:**
- ISO 3166-1 Countries (`iso_3166_1`, 271 nodes: 5 continents, 17 sub-regions, 249 countries)
- ISO 3166-2 Subdivisions (`iso_3166_2`, ~5,246 nodes)
- ISO 3166 crosswalk (~498 edges)
- UN M.49 Geographic Regions (`un_m49`, 272 nodes)
- UN M.49 / ISO 3166-1 crosswalk (~498 edges)

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

**REST API (FastAPI):**
- Full browse, search, translate, compare, diff, and auth endpoints

**MCP Server (20 tools, stdio transport)**

**Auth system:** JWT tokens, API keys with `wot_` prefix, rate limiting

**Next.js 15 frontend:** Industry Map, Galaxy View, System detail, Node detail, Explore, Dashboard

**Infrastructure:** 277 tests (pytest), Neon PostgreSQL, test_wot schema isolation

### Database

- `classification_system`: 10 rows
- `classification_node`: 10,966 rows
- `equivalence`: 11,420 rows

---

[Unreleased]: https://github.com/colaberry/WorldOfTaxanomy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/colaberry/WorldOfTaxanomy/releases/tag/v0.1.0
