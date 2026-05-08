# Technology Standards and Specifications

> **TL;DR:** WoT hosts ~25 technology-standards taxonomies that don't fit cleanly into the industry / regulatory / academic / financial buckets but still describe stable enumerated value spaces: telecom and networking specs (3GPP, ITU-T, ITU-R, IETF RFC, IEEE), connectivity (Bluetooth, USB, PCI-SIG, JEDEC, SEMI, VESA), web/internet (MIME types, HTTP status codes, SPDX licenses), cybersecurity catalogs (MITRE ATT&CK, CVE types, OWASP Top 10), AI / cloud-native taxonomies (AI Model Types, Cloud Native Landscape), and supplementary engineering / scientific reference (SI Units, Container ISO 6346, Periodic Table grouping is in environmental). Plus a handful of regulatory administrative anchors that don't belong in regulatory-standards.md (CFR Titles, USC Titles, IRS Forms, VAT Rate Types).

---

## Telecom and networking standards

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `3gpp_specs` | 18 | 3GPP | 3GPP technical specifications (cellular, 5G, etc.) |
| `itu_t` | 19 | ITU-T | International Telecommunication Union telecom recommendations |
| `itu_r_bands` | 16 | ITU-R | ITU-R radio frequency band designations |
| `ietf_rfc` | 15 | IETF | IETF RFC categorical groupings |
| `ieee_standards` | 14 | IEEE | IEEE standards (skeleton; 802.x family, etc.) |

## Connectivity and hardware specifications

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `bluetooth_profiles` | 17 | Bluetooth SIG | Bluetooth Special Interest Group profiles |
| `usb_classes` | 23 | USB-IF | USB Implementers Forum device class codes |
| `pci_sig` | 14 | PCI-SIG | PCI Special Interest Group specifications |
| `jedec` | 14 | JEDEC | Joint Electron Device Engineering Council standards |
| `semi_standards` | 14 | SEMI | Semiconductor Equipment and Materials International standards |
| `vesa_standards` | 13 | VESA | Video Electronics Standards Association specifications |

## Web, internet, and software

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `mime_types` | 16 | IANA | Media (MIME) type categories |
| `http_status` | 17 | IETF / IANA | HTTP status code classes (1xx-5xx and detail) |
| `spdx_licenses` | 17 | Linux Foundation | SPDX License List groupings |
| `ai_model_type` | 17 | curated | AI / ML model types (curated WoT vocabulary) |
| `cloud_native` | 15 | CNCF | Cloud Native Computing Foundation landscape categories |

## Cybersecurity catalogs

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `mitre_attack` | 15 | MITRE | MITRE ATT&CK adversary tactics and techniques |
| `cve_types` | 16 | MITRE | CVE / CWE vulnerability and weakness type categories |
| `owasp_top10` | 11 | OWASP | OWASP Top 10 web application security risks |
| `wcag` | 17 | W3C | Web Content Accessibility Guidelines (WCAG 2.x) |

WCAG sits here for taxonomic reasons (it's a W3C specification with stable success-criterion identifiers) even though its primary use is accessibility compliance, which overlaps the Regulatory Standards page.

## Engineering and scientific reference

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `si_units` | 19 | BIPM | SI base and derived unit categories |
| `container_iso` | 14 | ISO 6346 | Standard intermodal container type codes |
| `nato_codification` | 19 | NATO | NATO Stock Number / Codification System (skeleton) |
| `dod_mil_std` | 15 | US DoD | US Department of Defense MIL-STD categories |
| `un_ammo` | 14 | UN ECOSOC | UN ammunition / dangerous-goods identification (IATG) |
| `stanag` | 16 | NATO | NATO Standardization Agreement categories |
| `isa_standards` | 12 | ISA | International Society of Automation standards |

## Regulatory administrative anchors

These are titling / numbering schemes rather than substantive regulations. They don't fit the [Regulatory Standards page](./regulatory-standards.md) (which covers regulations themselves) but are stable enumerated taxonomies often referenced when citing regulations.

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `cfr_titles` | 19 | US OFR | Code of Federal Regulations title list (Title 1 through 50) |
| `cfr_title_49` | 104 | US DOT (USDOT) | CFR Title 49 (Transportation) detailed parts |
| `usc_titles` | 23 | US OLRC | US Code title list |
| `irs_forms` | 15 | IRS | IRS form-type categories |
| `vat_rates` | 14 | various | VAT rate types (standard, reduced, super-reduced, zero) |
| `gdpr_articles` | 110 | EDPB | GDPR article-level breakdown (companion to `reg_eu_ai_act` / `reg_eprivacy` for legal-tech use) |
| `gdpr_basis` | 16 | EDPB | GDPR Article 6 lawful bases + special-category Article 9 bases |
| `gdpr_rights` | 13 | EDPB | GDPR data-subject rights (access, rectification, erasure, etc.) |
| `data_retention` | 16 | curated | Data retention period categories (curated WoT vocabulary) |

## Other technical reference

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `iso_31000` | 47 | ISO | ISO 31000 risk management principles and process |
| `gri_standards` | 38 | GRI | Global Reporting Initiative sustainability reporting standards (companion to env / financial pages) |
| `tcfd` | 14 | TCFD | TCFD recommendations (companion to financial-systems page) |
| `gs1_standards` | 14 | GS1 | GS1 standards meta-catalog (parent of GS1 GPC, GTIN, etc.) |
| `edi_standards` | 14 | various | EDI standards categorization (X12, EDIFACT, etc.) |

## Logistics and freight

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `nmfc` | 19 | NMFTA | National Motor Freight Classification |
| `stcc` | 26 | AAR | Standard Transportation Commodity Code |
| `imo_ship_type` | 17 | IMO | IMO ship type classification |
| `imo_vessel` | 17 | IMO | IMO vessel type categories |
| `iata_aircraft` | 14 | IATA | IATA aircraft type codes |
| `faa_aircraft_cat` | 16 | FAA | FAA aircraft category and class designations |
| `uic_railway` | 15 | UIC | UIC railway codes |
| `icao_doc4444` | 15 | ICAO | ICAO flight rules and procedures (Doc 4444) |
| `wco_safe` | 14 | WCO | World Customs Organization SAFE Framework of Standards |

## Trade tariff / customs minor systems

These complement the main [Trade Codes page](./trade-codes.md) which covers HS, CPC, UNSPSC, SITC, BEC.

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `eu_taric` | 22 | European Commission | EU TARIC (Integrated Tariff of the European Union) |
| `uk_trade_tariff` | 22 | UK Government | UK Trade Tariff |
| `gcc_tariff` | 17 | GCC | Gulf Cooperation Council common tariff |
| `ecowas_cet` | 14 | ECOWAS | ECOWAS Common External Tariff |
| `prodcom` | 38 | Eurostat | EU PRODCOM (industrial production statistics) |
| `cpv_2008` | 96 | European Commission | Common Procurement Vocabulary 2008 |
| `coicop` | 62 | UN | Classification of Individual Consumption According to Purpose |
| `eccn` | 58 | US BIS | Export Control Classification Number |
| `schedule_b` | 119 | US Census | Schedule B export classification |
| `hts_us` | 120 | USITC | Harmonized Tariff Schedule of the United States |

## Sports, culture, miscellaneous

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `olympic_sports` | 16 | IOC | Olympic sports categories |
| `fifa_confederations` | 14 | FIFA | FIFA football confederations |
| `pantone_families` | 12 | Pantone | Pantone color family groupings |
| `ral_colors` | 13 | RAL | RAL color standard families |
| `isrc_format` | 13 | IFPI | International Standard Recording Code structure |
| `isbn_groups` | 13 | International ISBN Agency | ISBN agency / language groups |
| `richter_scale` | 13 | various | Richter / earthquake magnitude scale |
| `usda_soil` | 13 | USDA | USDA soil taxonomy (skeleton; companion to environmental) |
| `oecd_dac` | 62 | OECD | OECD Development Assistance Committee sector codes |
| `seea` | 47 | UN | System of Environmental-Economic Accounting (SEEA) |
| `lme_metals` | 15 | LME | London Metal Exchange traded metals |
| `opec_basket` | 14 | OPEC | OPEC reference basket of crude oils |
| `naic_lines` | 30 | NAIC | NAIC insurance lines of business (companion to financial-systems) |
| `haccp` | 13 | Codex Alimentarius | HACCP food-safety principles |
| `codex_committees` | 19 | FAO / WHO | Codex Alimentarius committee structure |
| `allergen_list` | 15 | EU | EU 14 major allergens (Annex II of Regulation 1169/2011) |
| `ibc_2021` | 26 | ICC | International Building Code 2021 |
| `nfpa_codes` | 17 | NFPA | National Fire Protection Association codes |
| `rics_valuation` | 14 | RICS | Royal Institution of Chartered Surveyors valuation standards |
| `contract_types` | 16 | curated | Contract type categories (curated WoT vocabulary) |
| `board_committee` | 14 | curated | Board / committee structure types (curated) |
| `shrm_competency` | 16 | SHRM | SHRM HR competency model |
| `job_family` | 19 | curated | Job family taxonomy (curated WoT vocabulary; complements occupation systems) |
| `emoji_categories` | 13 | Unicode Consortium | Unicode emoji category groupings |
| `breeam` | 17 | BRE | BREEAM (also referenced in environmental-standards) |
| `leed_v4_1` | 14 | USGBC | LEED v4.1 (also referenced in environmental-standards) |

## Why this is a "miscellaneous" page

The systems above are real, published, stable, and within size cap (per the [Inclusion Policy](./inclusion-policy.md)) - so they belong in WoT - but they don't form a coherent topical cluster that justifies a dedicated page on its own. Putting them here keeps them findable while honoring the Karpathy four-channel pattern: catalog row plus topical context plus llms-full.txt presence plus wiki API exposure.

If your downstream product cares about a specific subset (say, telecom standards or cybersecurity catalogs), filter by system_id prefix at the API:

```bash
GET /api/v1/systems?prefix=itu_
GET /api/v1/systems?prefix=mitre_
```

## Related reading

- [Inclusion Policy](./inclusion-policy.md) - why these qualify even though they're small.
- [Regulatory Standards](./regulatory-standards.md) - GDPR, NIST, ISO management standards (complements the GDPR-articles entry on this page).
- [Process and Activity Frameworks](./process-frameworks.md) - APQC PCF, SCOR, ITIL 4 (overlaps WCAG and ISO 31000 conceptually).
