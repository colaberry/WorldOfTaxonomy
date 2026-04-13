# Data Sources

Attribution and licensing for all classification systems in WorldOfTaxanomy.

WorldOfTaxanomy does NOT redistribute raw data files. Every ingester downloads data directly from the authoritative source at ingest time (or requires manual download where license terms prohibit automated access). The ingested structured data in the database is derived from these sources and remains under the original licenses.

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
| `domain_truck_freight` | Truck Freight Types | WorldOfTaxanomy | Open | Mode, equipment, service level, cargo type |
| `domain_truck_vehicle` | Truck Vehicle Classes | WorldOfTaxanomy / DOT | Public domain | DOT GVWR Classes 1-8 + body types |
| `domain_truck_cargo` | Truck Cargo Classification | WorldOfTaxanomy | Open | NMFC-pattern commodity groups + DOT hazmat classes 1-9 |
| `domain_truck_ops` | Truck Carrier Operations | WorldOfTaxanomy / FMCSA | Public domain | Carrier type, fleet size, business model, route pattern |

### Domain Deep-Dives (Agriculture, Mining, Utilities, Construction, Cross-sector)

| System ID | Full Name | Authority | License |
|-----------|-----------|-----------|---------|
| `domain_ag_crop` | Agricultural Crop Types | WorldOfTaxanomy / USDA | Open |
| `domain_ag_livestock` | Agricultural Livestock Categories | WorldOfTaxanomy | Open |
| `domain_ag_method` | Agricultural Farming Methods | WorldOfTaxanomy | Open |
| `domain_ag_grade` | Agricultural Commodity Grades | WorldOfTaxanomy / USDA | Open |
| `domain_mining_mineral` | Mining Mineral Types | WorldOfTaxanomy | Open |
| `domain_mining_method` | Mining Extraction Methods | WorldOfTaxanomy | Open |
| `domain_mining_reserve` | Mining Reserve Classification | WorldOfTaxanomy / SPE-PRMS | Open |
| `domain_util_energy` | Utility Energy Sources | WorldOfTaxanomy / IEA | Open |
| `domain_util_grid` | Utility Grid Regions | WorldOfTaxanomy / NERC | Open |
| `domain_const_trade` | Construction Trade Types | WorldOfTaxanomy | Open |
| `domain_const_building` | Construction Building Types | WorldOfTaxanomy | Open |
| `domain_mfg_process` | Manufacturing Process Types | WorldOfTaxanomy | Open |
| `domain_retail_channel` | Retail Channel Types | WorldOfTaxanomy | Open |
| `domain_finance_instrument` | Finance Instrument Types | WorldOfTaxanomy | Open |
| `domain_health_setting` | Health Care Settings | WorldOfTaxanomy | Open |
| `domain_transport_mode` | Transportation Modes | WorldOfTaxanomy | Open |
| `domain_info_media` | Information and Media Types | WorldOfTaxanomy | Open |
| `domain_realestate_type` | Real Estate Property Types | WorldOfTaxanomy | Open |
| `domain_food_service` | Food Service and Accommodation Types | WorldOfTaxanomy | Open |
| `domain_wholesale_channel` | Wholesale Trade Channels | WorldOfTaxanomy | Open |
| `domain_prof_services` | Professional Services Types | WorldOfTaxanomy | Open |
| `domain_education_type` | Education Program Types | WorldOfTaxanomy | Open |
| `domain_arts_content` | Arts and Entertainment Content Types | WorldOfTaxanomy | Open |
| `domain_other_services` | Other Services Types | WorldOfTaxanomy | Open |
| `domain_public_admin` | Public Administration Types | WorldOfTaxanomy | Open |
| `domain_supply_chain` | Supply Chain and Trade Terms | WorldOfTaxanomy | Open |
| `domain_workforce_safety` | Workforce Safety and Health | WorldOfTaxanomy / OSHA | Open |

### Magna Compass Emerging Sector Domain Taxonomies

All hand-coded by WorldOfTaxanomy, open license.

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

---

## Notes on Licensing

- **Public domain** systems (NAICS, SIC, CFR, FMCSA) may be used, modified, and redistributed freely.
- **CC BY 4.0** systems (ANZSIC, ISCO-08, ESCO, O*NET, ATC) require attribution when redistributed. Attribution is provided above.
- **Open** systems (ISIC, NACE, NIC, COFOG, etc.) are freely available from their respective statistical agencies.
- **GICS Bridge**: Contains only the 11 publicly known sector names available in financial press. No proprietary GICS data is stored or redistributed.
- **ICD-11**: Requires manual download from icd.who.int. The CC BY-ND 3.0 IGO license prohibits automated redistribution of derivative works.
- **LOINC**: Requires free registration and manual download from loinc.org. The Regenstrief LOINC License prohibits automated download.
- The WorldOfTaxanomy codebase is MIT licensed. Ingested classification data remains under its original license.

---

## Reporting a Licensing Issue

If you believe any data is being used in violation of its license, please open a GitHub issue immediately at https://github.com/colaberry/WorldOfTaxanomy/issues.
