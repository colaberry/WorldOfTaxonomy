# Data Sources

Attribution and licensing for all classification systems in WorldOfTaxonomy.

WorldOfTaxonomy does NOT redistribute raw data files. Every ingester downloads data directly from the authoritative source at ingest time (or requires manual download where license terms prohibit automated access). The ingested structured data in the database is derived from these sources and remains under the original licenses.

The canonical, always-current list of systems is `GET /api/v1/systems` (1,000+ entries today). The tables below highlight primary sources per category. `CLAUDE.md` carries a full row-per-system inventory mirrored from the database.

---

## Classification Systems

### Industry Classification

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `naics_2022` | North American Industry Classification System | 2022 | US Census Bureau | Public domain | https://www.census.gov/naics/ |
| `isic_rev4` | International Standard Industrial Classification | Rev 4 | UN Statistics Division | Open (CC BY) | https://unstats.un.org/unsd/classifications/Econ/isic |
| `nace_rev2` | Statistical Classification of Economic Activities in the EC | Rev 2 | Eurostat | Open | https://ec.europa.eu/eurostat/ramon/ |
| `sic_1987` | Standard Industrial Classification | 1987 | OSHA / US Dept of Labor | Public domain | https://www.osha.gov/data/sic-manual |
| `anzsic_2006` | Australian and NZ Standard Industrial Classification | 2006 | Australian Bureau of Statistics | CC BY 4.0 | https://www.abs.gov.au/ANZSIC |
| `nic_2008` | National Industrial Classification | 2008 | Ministry of Statistics, India | Open | https://mospi.gov.in/classification/national-industrial-classification |
| `wz_2008` | Klassifikation der Wirtschaftszweige | 2008 | Statistisches Bundesamt | Open | https://www.destatis.de/DE/Methoden/Klassifikationen/ |
| `onace_2008` | Osterreichische Systematik der Wirtschaftstatigkeiten | 2008 | Statistik Austria | Open | https://www.statistik.at/ |
| `noga_2008` | Nomenclature generale des activites economiques | 2008 | Swiss Federal Statistical Office | Open | https://www.bfs.admin.ch/ |
| `jsic_2013` | Japan Standard Industrial Classification | 2013 | Statistics Bureau of Japan | Open | https://www.stat.go.jp/english/ |

### Geography

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `iso_3166_1` | ISO 3166-1 Countries (with UN M.49 regional hierarchy) | 2023 | ISO / UN Statistics Division | CC0 | https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes |
| `iso_3166_2` | ISO 3166-2 Country Subdivisions | 2023 | ISO (via pycountry) | LGPL (library); ISO data public | https://pypi.org/project/pycountry/ |
| `un_m49` | UN M.49 Standard Country or Area Codes | 2023 | UN Statistics Division | Open | https://unstats.un.org/unsd/methodology/m49/overview |

### Product and Trade

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `hs_2022` | Harmonized Commodity Description and Coding System | 2022 | World Customs Organization | CC0 (via datasets/harmonized-system) | https://github.com/datasets/harmonized-system |
| `cpc_v21` | Central Product Classification | v2.1 | UN Statistics Division | Open | https://unstats.un.org/unsd/classifications/Econ/cpc |
| `unspsc_v24` | Universal Standard Products and Services Code | v24 | GS1 US (via Oklahoma Open Data) | Public domain | https://data.ok.gov/dataset/unspsc-codes |

### Occupational

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `soc_2018` | Standard Occupational Classification | 2018 | US Bureau of Labor Statistics | Public domain | https://www.bls.gov/soc/ |
| `isco_08` | International Standard Classification of Occupations | 2008 | International Labour Organization | CC BY 4.0 | https://www.ilo.org/public/english/bureau/stat/isco/ |
| `esco_occupations` | ESCO Occupations | v1.1.1 | European Commission | CC BY 4.0 | https://esco.ec.europa.eu/en/use-esco/download |
| `esco_skills` | ESCO Skills and Competences | v1.1.1 | European Commission | CC BY 4.0 | https://esco.ec.europa.eu/en/use-esco/download |
| `onet_soc` | O*NET Occupational Information Network | 29.0 | US Dept of Labor / ETA | CC BY 4.0 | https://www.onetcenter.org/database.html |

### Education

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `cip_2020` | Classification of Instructional Programs | 2020 | National Center for Education Statistics | Public domain | https://nces.ed.gov/ipeds/cipcode/ |
| `iscedf_2013` | International Standard Classification of Education (Fields) | 2013 | UNESCO Institute for Statistics | Open | https://uis.unesco.org/ |

### Health and Pharmaceutical

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `atc_who` | Anatomical Therapeutic Chemical Classification | 2021 | WHO / WHOCC (via fabkury/atcd) | CC BY 4.0 | https://github.com/fabkury/atcd |
| `icd_11` | International Classification of Diseases 11th Revision | ICD-11 MMS | World Health Organization | CC BY-ND 3.0 IGO | https://icd.who.int/browse/latest/mms/en (SimpleTabulation download; 37,052 nodes from zip) |
| `loinc` | Logical Observation Identifiers Names and Codes | - | Regenstrief Institute | Regenstrief LOINC License | https://loinc.org/ (manual download + free registration required) |

### Financial and Environmental

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `cofog` | Classification of Functions of Government | - | UN Statistics Division | Open | https://unstats.un.org/unsd/classifications/Econ/cofog |
| `gics_bridge` | Global Industry Classification Standard Bridge (11 sectors only) | - | MSCI / S&P | Proprietary - sector names only | https://www.msci.com/gics |
| `ghg_protocol` | Greenhouse Gas Protocol Scope Categories | - | WRI / WBCSD (hand-coded) | Open | https://ghgprotocol.org/ |

### Skills and Innovation

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `patent_cpc` | Cooperative Patent Classification | 2024 | EPO / USPTO | Open (EPO) | https://www.cooperativepatentclassification.org/ |

### Regulatory

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `cfr_title_49` | Code of Federal Regulations Title 49 (Transportation) | - | US Government (hand-coded) | Public domain | https://www.ecfr.gov/current/title-49 |
| `fmcsa_regs` | Federal Motor Carrier Safety Administration Regulations | - | FMCSA / DOT (hand-coded) | Public domain | https://www.fmcsa.dot.gov/regulations |
| `gdpr_articles` | General Data Protection Regulation Articles | 2018 | European Union (hand-coded from EUR-Lex) | Open | https://gdpr-info.eu/ |
| `iso_31000` | ISO 31000 Risk Management Guidelines | 2018 | ISO (hand-coded from public structure) | Open (structure only) | https://www.iso.org/standard/65694.html |

### Occupational (additional)

| System ID | Full Name | Version | Authority | License | URL |
|-----------|-----------|---------|-----------|---------|-----|
| `anzsco_2022` | Australian and NZ Standard Classification of Occupations | 2022 | Australian Bureau of Statistics | CC BY 4.0 | https://www.abs.gov.au/ANZSCO |

### Domain Deep-Dives (Truck Transportation - NAICS 484)

| System ID | Full Name | Authority | License | Notes |
|-----------|-----------|-----------|---------|-------|
| `domain_truck_freight` | Truck Freight Types | WorldOfTaxonomy | Open | Mode, equipment, service level, cargo type |
| `domain_truck_vehicle` | Truck Vehicle Classes | WorldOfTaxonomy / DOT | Public domain | DOT GVWR Classes 1-8 + body types |
| `domain_truck_cargo` | Truck Cargo Classification | WorldOfTaxonomy | Open | NMFC-pattern commodity groups + DOT hazmat classes 1-9 |
| `domain_truck_ops` | Truck Carrier Operations | WorldOfTaxonomy / FMCSA | Public domain | Carrier type, fleet size, business model, route pattern |

### Domain Deep-Dives (Agriculture, Mining, Utilities, Construction, Cross-sector)

| System ID | Full Name | Authority | License |
|-----------|-----------|-----------|---------|
| `domain_ag_crop` | Agricultural Crop Types | WorldOfTaxonomy / USDA | Open |
| `domain_ag_livestock` | Agricultural Livestock Categories | WorldOfTaxonomy | Open |
| `domain_ag_method` | Agricultural Farming Methods | WorldOfTaxonomy | Open |
| `domain_ag_grade` | Agricultural Commodity Grades | WorldOfTaxonomy / USDA | Open |
| `domain_mining_mineral` | Mining Mineral Types | WorldOfTaxonomy | Open |
| `domain_mining_method` | Mining Extraction Methods | WorldOfTaxonomy | Open |
| `domain_mining_reserve` | Mining Reserve Classification | WorldOfTaxonomy / SPE-PRMS | Open |
| `domain_util_energy` | Utility Energy Sources | WorldOfTaxonomy / IEA | Open |
| `domain_util_grid` | Utility Grid Regions | WorldOfTaxonomy / NERC | Open |
| `domain_const_trade` | Construction Trade Types | WorldOfTaxonomy | Open |
| `domain_const_building` | Construction Building Types | WorldOfTaxonomy | Open |
| `domain_mfg_process` | Manufacturing Process Types | WorldOfTaxonomy | Open |
| `domain_retail_channel` | Retail Channel Types | WorldOfTaxonomy | Open |
| `domain_finance_instrument` | Finance Instrument Types | WorldOfTaxonomy | Open |
| `domain_health_setting` | Health Care Settings | WorldOfTaxonomy | Open |
| `domain_transport_mode` | Transportation Modes | WorldOfTaxonomy | Open |
| `domain_info_media` | Information and Media Types | WorldOfTaxonomy | Open |
| `domain_realestate_type` | Real Estate Property Types | WorldOfTaxonomy | Open |
| `domain_food_service` | Food Service and Accommodation Types | WorldOfTaxonomy | Open |
| `domain_wholesale_channel` | Wholesale Trade Channels | WorldOfTaxonomy | Open |
| `domain_prof_services` | Professional Services Types | WorldOfTaxonomy | Open |
| `domain_education_type` | Education Program Types | WorldOfTaxonomy | Open |
| `domain_arts_content` | Arts and Entertainment Content Types | WorldOfTaxonomy | Open |
| `domain_other_services` | Other Services Types | WorldOfTaxonomy | Open |
| `domain_public_admin` | Public Administration Types | WorldOfTaxonomy | Open |
| `domain_supply_chain` | Supply Chain and Trade Terms | WorldOfTaxonomy | Open |
| `domain_workforce_safety` | Workforce Safety and Health | WorldOfTaxonomy / OSHA | Open |

### Country-specific industry classifications (national adaptations)

Beyond the flagship industry systems above, WorldOfTaxonomy ingests every publicly available national adaptation of ISIC Rev 4 and NACE Rev 2 (200+ systems). These are sourced from the national statistical office of each country (e.g. INEGI for Mexico's SCIAN, IBGE for Brazil's CNAE, Rosstat for Russia's OKVED-2, INE for Spain's CNAE 2009) and licensed per each office's terms (typically open data / public domain). See `GET /api/v1/systems?region={code}` for the canonical per-country list.

### Regulatory, compliance, and standards systems

WorldOfTaxonomy covers 200+ regulatory and standards systems including GDPR, HIPAA, SOX, FISMA, FedRAMP, OSHA 29 CFR 1910/1926, NERC CIP, PCI DSS, NIST CSF, SOC 2, HITRUST, CMMC, DORA, NIS2, EU AI Act, MiFID II, Solvency II, REACH, MDR, CSRD, Basel III/IV, FATF 40, and the full ISO management-system family (9001, 14001, 27001, 45001, 22000, etc.). Each is ingested from its authoritative source (EUR-Lex, ecfr.gov, ISO, NIST, etc.) under the applicable open or public-domain license for the structure; full clause-level text remains under the original publisher's terms.

### Health and life sciences systems

Beyond ATC, ICD-11, and LOINC above: ICD-10-CM, ICD-10-PCS, ICD-10-GM, ICD-10-AM, ICD-10-CA, ICD-O-3, ICF, ICPC-2, ICHI, MeSH, NCI Thesaurus, RxNorm (skeleton), NDC, DSM-5 (skeleton), SNOMED CT (skeleton), CPT (AMA skeleton), G-DRG, GBD Cause List, GMDN, WHO Essential Medicines, CDC Vaccine Schedule, CTCAE, HL7 FHIR resources, DICOM modalities. Sources: CDC, NLM, WHO, Regenstrief, AMA, DIMDI, IHTSDO/SNOMED International (skeleton only for proprietary systems), with licenses per publisher.

### Magna Compass Emerging Sector Domain Taxonomies

All hand-coded by WorldOfTaxonomy, open license.

| System ID | Full Name | Codes |
|-----------|-----------|-------|
| `domain_chemical_type` | Chemical Industry Types | 29 |
| `domain_defence_type` | Defence and Security Types | 23 |
| `domain_water_env` | Water and Environment Types | 28 |
| `domain_ai_data` | AI and Data Types | 25 |
| `domain_biotech` | Biotechnology and Genomics Types | 26 |
| `domain_space` | Space and Satellite Economy Types | 24 |
| `domain_climate_tech` | Climate Technology Types | 30 |
| `domain_adv_materials` | Advanced Materials Types | 27 |
| `domain_quantum` | Quantum Computing Types | 23 |
| `domain_digital_assets` | Digital Assets and Web3 Types | 25 |
| `domain_robotics` | Autonomous Systems and Robotics Types | 27 |
| `domain_energy_storage` | New Energy Storage Types | 25 |
| `domain_semiconductor` | Next-Generation Semiconductor Types | 31 |
| `domain_synbio` | Synthetic Biology Types | 28 |
| `domain_xr_meta` | Extended Reality and Metaverse Types | 27 |

---

## Crosswalk Edges

Every row in `equivalence` carries a `provenance` column identifying where the edge came from, and every API response attaches a computed `edge_kind` (one of `standard_standard`, `standard_domain`, `domain_standard`, `domain_domain`) so clients can filter authoritative statistical concordances from generated bridges.

### Provenance values

| Provenance tag | Meaning | Authority |
|----------------|---------|-----------|
| _null or authority-named_ (e.g. `UN Statistics Division`, `Eurostat`, `US BLS`, `WITS`) | Ingested from an authoritative statistical concordance | External publisher |
| `derived:nace_national:v1` | 1:1 structural parallel between NACE Rev 2 and a national NACE adaptation (WZ 2008, ONACE 2008, NOGA 2008, CAE Rev 3, CZ-NACE, etc.) | WorldOfTaxonomy |
| `derived:sector_anchor:v1` | Generated bridge edge anchoring a domain taxonomy node to a NAICS 2022 node via sector-prefix rules in `domain_anchors.json` | WorldOfTaxonomy |
| `derived:sector_anchor:v1:fanout` | Parallel edge fanned out from a `derived:sector_anchor:v1` NAICS anchor to the equivalent ISIC Rev 4 or NACE Rev 2 node | WorldOfTaxonomy |

Generated bridges (`derived:sector_anchor:v1*`) are always `match_type='broad'`. Callers that want only authoritative statistical crosswalks should filter `?match_type=exact` or `?edge_kind=standard_standard`.

### Authoritative concordances

| Crosswalk | Approx. Edges | Source | License |
|-----------|---------------|--------|---------|
| NAICS 2022 / ISIC Rev 4 | ~698 | UN Statistics Division concordance | Open |
| ISO 3166-1 / ISO 3166-2 | ~498 | Derived from iso3166_all.csv | CC0 |
| UN M.49 / ISO 3166-1 | ~498 | Derived from country code data | CC0 |
| HS 2022 / ISIC Rev 4 | ~3,010 | World Bank WITS concordance | CC BY 4.0 |
| CPC v2.1 / ISIC Rev 4 | ~5,430 | UN Statistics Division CPCv21_ISIC4 | Open |
| HS 2022 / CPC v2.1 | ~11,686 | UN Statistics Division CPCv21_HS2017 | Open |
| NACE Rev 2 / WZ 2008 | ~996 | Derived (WZ is a national NACE adaptation) | Open |
| NACE Rev 2 / ONACE 2008 | ~996 | Derived (ONACE is a national NACE adaptation) | Open |
| NACE Rev 2 / NOGA 2008 | ~996 | Derived (NOGA is a national NACE adaptation) | Open |
| SOC 2018 / ISCO-08 | ~1,984 | ILO / BLS concordance | Public domain / CC BY 4.0 |
| CIP 2020 / SOC 2018 | ~2,000 | US Dept of Education | Public domain |
| CIP 2020 / ISCED-F 2013 | ~122 | Derived from field-of-study mappings | Open |
| ESCO Occupations / ISCO-08 | ~2,942 | ESCO provides the mapping | CC BY 4.0 |
| O*NET-SOC / SOC 2018 | ~867 | Derived (O*NET extends SOC 2010 codes) | CC BY 4.0 |
| CFR Title 49 / NAICS | ~300 | Derived from regulatory scope | Public domain |
| FMCSA Regs / Truck Domain Taxonomies | ~50 | Derived from regulatory scope | Public domain |
| NAICS 484 / Truck Domain Taxonomies | ~200 | Derived from industry scope | Open |
| NAICS 11 / Agriculture Domain Taxonomies | ~48 | Derived from industry scope | Open |
| NAICS 21 / Mining Domain Taxonomies | ~31 | Derived from industry scope | Open |
| NAICS 22 / Utility Domain Taxonomies | ~20 | Derived from industry scope | Open |
| NAICS 23 / Construction Domain Taxonomies | ~27 | Derived from industry scope | Open |
| ANZSCO 2022 / ANZSIC 2006 | ~1,590 | ABS concordance | CC BY 4.0 |
| ISCO-08 / ISIC Rev 4 | ~500 | ILO concordance | CC BY 4.0 |
| Nation-Sector Geographic Synergy | 98 | Hand-coded (ISO 3166-1 -> NAICS 2-digit sectors) | Open |
| Country-System Applicability | ~310 | Hand-coded (ISO 3166-1 alpha-2 -> classification systems) | Open |

### Derived crosswalks (sector-anchor generator)

| Crosswalk family | Approx. Edges | Provenance | How it's generated |
|------------------|---------------|------------|--------------------|
| Domain taxonomy -> NAICS 2022 (sector anchors) | ~2,500 | `derived:sector_anchor:v1` | `world_of_taxonomy/ingest/crosswalk_domain_anchors.py` walks every `domain_*` node and applies per-system prefix rules from `domain_anchors.json` to emit a `broad` edge to the matching NAICS sector |
| Domain -> ISIC Rev 4 / NACE Rev 2 (fan-out) | ~2,200 | `derived:sector_anchor:v1:fanout` | For each `derived:sector_anchor:v1` NAICS edge, the fan-out ingester emits parallel edges to the equivalent ISIC Rev 4 and NACE Rev 2 nodes using the NAICS -> ISIC concordance and NACE parallels |

All 434 curated domain taxonomies are reachable from NAICS / ISIC / NACE through one of these two generated edge families. Counts fluctuate as new domain systems are added; run `GET /api/v1/equivalences/stats?group_by=edge_kind` for a live breakdown.

---

## Notes on Licensing

- **Public domain** systems (NAICS, SIC, CFR, FMCSA) may be used, modified, and redistributed freely.
- **CC BY 4.0** systems (ANZSIC, ISCO-08, ESCO, O*NET, ATC) require attribution when redistributed. Attribution is provided above.
- **Open** systems (ISIC, NACE, NIC, COFOG, etc.) are freely available from their respective statistical agencies.
- **GICS Bridge**: Contains only the 11 publicly known sector names available in financial press. No proprietary GICS data is stored or redistributed.
- **ICD-11**: Requires manual download from icd.who.int. The CC BY-ND 3.0 IGO license prohibits automated redistribution of derivative works.
- **LOINC**: Requires free registration and manual download from loinc.org. The Regenstrief LOINC License prohibits automated download.
- The WorldOfTaxonomy codebase is MIT licensed. Ingested classification data remains under its original license.

---

## Reporting a Licensing Issue

If you believe any data is being used in violation of its license, please open a GitHub issue immediately at https://github.com/colaberry/WorldOfTaxonomy/issues.
