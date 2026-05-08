# Environmental Standards and Scales

> **TL;DR:** WoT hosts ~30 environmental classification systems across four families: green-building rating schemes (BREEAM, LEED), biodiversity and conservation taxonomies (IUCN Red List, CITES, Ramsar, CBD targets, UNEP Chemicals), waste and chemicals codes (EPA RCRA, EU Waste Catalogue, Stockholm/Rotterdam/Minamata Conventions), climate and energy data taxonomies (GHG Protocol, IEA Energy Balance, IRENA, FAO AQUASTAT, FAOSTAT, ISO 14001/14040/14064/50001), and natural-science scales (Beaufort, Saffir-Simpson, Fujita, UV Index, Köppen Climate, Geological Timescale, Periodic Table). Plus the SDG 2030 framework and the TNFD nature-related disclosure standard.

---

## Green building and infrastructure

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `breeam` | 17 | BRE | Building Research Establishment Environmental Assessment Method |
| `leed_v4_1` | 14 | USGBC | Leadership in Energy and Environmental Design v4.1 |
| `reg_iso_14001` | 29 | ISO | Environmental management system standard |
| `reg_iso_50001` | 26 | ISO | Energy management system standard |

## Biodiversity and conservation

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `iucn_red_list` | 15 | IUCN | Red List of Threatened Species categories |
| `cites` | 16 | CITES Secretariat | Convention on International Trade in Endangered Species (Appendix I/II/III) |
| `ramsar` | 21 | Ramsar Convention | Ramsar wetland classification |
| `cbd_targets` | 24 | CBD Secretariat | Convention on Biological Diversity Global Biodiversity Framework targets |
| `cbd_aichi` | 21 | CBD Secretariat | Aichi Biodiversity Targets (legacy 2011-2020 framework, still cited) |

## Waste, chemicals, and pollution

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `epa_rcra_waste` | 15 | US EPA | Hazardous waste codes under RCRA |
| `eu_waste_cat` | 21 | European Commission | EU Waste Catalogue (2014/955/EU) |
| `stockholm_pops` | 19 | Stockholm Convention | Persistent Organic Pollutants Annex A/B/C |
| `rotterdam_pic` | 17 | Rotterdam Convention | Prior Informed Consent procedure for hazardous chemicals |
| `minamata` | 15 | Minamata Convention | Mercury phase-out provisions |
| `unep_chemicals` | 15 | UNEP | UNEP chemicals categories |

## Climate, energy, and natural resources

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `ghg_protocol` | 20 | WRI / WBCSD | Greenhouse Gas Protocol (Scope 1/2/3 categories) |
| `reg_iso_14064` | 20 | ISO | GHG quantification, monitoring, verification |
| `reg_iso_14040` | 25 | ISO | Life-cycle assessment principles and framework |
| `iea_energy_bal` | 19 | IEA | International Energy Agency energy balance categories |
| `irena_re` | 17 | IRENA | International Renewable Energy Agency RE technology types |
| `fao_aquastat` | 14 | FAO | Global water and agriculture statistics taxonomy |
| `fao_stat_domain` | 17 | FAO | FAOSTAT data domains (Production, Trade, Inputs, etc.) |

## Sustainability disclosure (overlap with regulatory and financial layers)

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `sdg` | 82 | United Nations | Sustainable Development Goals 2030 (17 goals + 169 targets, here ~82 nodes) |
| `un_sdg_indicators` | 20 | United Nations | SDG indicator framework |
| `tnfd` | 34 | TNFD | Taskforce on Nature-related Financial Disclosures |

See [Regulatory Standards](./regulatory-standards.md) for the broader sustainability-disclosure regulation set (CSRD, EU Taxonomy, SFDR, SBTi, ISSB S1/S2, etc.).

## Natural-science scales (small bounded enumerations)

These are short, stable, universal scales used as reference data across many domains.

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `beaufort_scale` | 14 | WMO | Beaufort Wind Force Scale (0-12 + extensions) |
| `saffir_simpson` | 12 | NHC / NOAA | Saffir-Simpson Hurricane Wind Scale (Cat 1-5 + extensions) |
| `fujita_tornado` | 10 | NWS | Enhanced Fujita Scale (EF0-EF5) |
| `uv_index` | 11 | WHO / WMO | Ultraviolet Index |
| `koppen_climate` | 17 | Köppen-Geiger | Köppen climate classification |
| `geological_time` | 20 | ICS | International Commission on Stratigraphy geologic time scale |
| `periodic_table` | 18 | IUPAC | Periodic table groupings (s/p/d/f-blocks, lanthanides, actinides, etc.) |

## Decision tree

| What you are doing | Use |
|---|---|
| Building energy / sustainability rating | `breeam` (UK/EU) or `leed_v4_1` (US/global) |
| Corporate GHG inventory | `ghg_protocol` + `reg_iso_14064` |
| Life-cycle environmental assessment | `reg_iso_14040` |
| Endangered-species trade compliance | `cites` |
| Wetland project classification | `ramsar` |
| Hazardous waste manifest | `epa_rcra_waste` (US) or `eu_waste_cat` (EU) |
| POPs / chemicals reporting | `stockholm_pops`, `rotterdam_pic`, `minamata` |
| Renewable-energy capacity reporting | `irena_re` |
| Tagging a research outcome to an SDG | `sdg` + `un_sdg_indicators` |
| Nature-related financial disclosure | `tnfd` |
| Categorizing a weather/climate observation | `beaufort_scale`, `saffir_simpson`, `fujita_tornado`, `koppen_climate` |

## Related reading

- [Regulatory Standards](./regulatory-standards.md) - EU sustainability regulations (CSRD, EU Taxonomy, SFDR, etc.).
- [Financial Systems](./financial-systems.md) - sustainable-finance frameworks (TNFD, SBTi, ISSB).
- [Inclusion Policy](./inclusion-policy.md) - rationale for what's in scope.
