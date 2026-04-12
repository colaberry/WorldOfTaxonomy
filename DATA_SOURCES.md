# Data Sources

Attribution and licensing information for all classification systems in WorldOfTaxanomy.

---

## Current Systems (v0.1.0)

| System | Full Name | Version | Region | Source | License | URL |
|--------|-----------|---------|--------|--------|---------|-----|
| `naics_2022` | North American Industry Classification System | 2022 | North America | US Census Bureau | Public domain | https://www.census.gov/naics/ |
| `isic_rev4` | International Standard Industrial Classification of All Economic Activities | Rev 4 | Global (UN) | United Nations Statistics Division | Open (CC BY 4.0 implied) | https://unstats.un.org/unsd/classifications/Econ/isic |
| `nace_rev2` | Statistical Classification of Economic Activities in the European Community | Rev 2 | European Union | Eurostat | Open | https://ec.europa.eu/eurostat/ramon/nomenclatures/index.cfm?TargetUrl=LST_NOM_DTL&StrNom=NACE_REV2 |
| `sic_1987` | Standard Industrial Classification | 1987 | USA/UK | OSHA / US Dept of Labor | Public domain | https://www.osha.gov/data/sic-manual |
| `anzsic_2006` | Australian and New Zealand Standard Industrial Classification | 2006 | Australia/NZ | Australian Bureau of Statistics | CC BY 4.0 | https://www.abs.gov.au/ANZSIC |
| `nic_2008` | National Industrial Classification | 2008 | India | Ministry of Statistics and Programme Implementation, India | Open | https://mospi.gov.in/classification/national-industrial-classification |
| `wz_2008` | Klassifikation der Wirtschaftszweige (German adaptation of NACE Rev 2) | 2008 | Germany | Statistisches Bundesamt (Destatis) | Open | https://www.destatis.de/DE/Methoden/Klassifikationen/Gueter-Wirtschaftsklassifikationen/klassifikation-wz-2008.html |
| `onace_2008` | Osterreichische Systematik der Wirtschaftstatigkeiten (Austrian adaptation of NACE Rev 2) | 2008 | Austria | Statistik Austria | Open | https://www.statistik.at/web_de/klassifikationen/oenace_2008/index.html |
| `noga_2008` | Nomenclature generale des activites economiques (Swiss adaptation of NACE Rev 2) | 2008 | Switzerland | Swiss Federal Statistical Office (FSO) | Open | https://www.bfs.admin.ch/bfs/en/home/statistics/industry-services/nomenclatures/noga.html |
| `jsic_2013` | Japan Standard Industrial Classification | 2013 | Japan | Statistics Bureau of Japan | Open | https://www.stat.go.jp/english/index/seido/sangyo/pdf/jsicrev13e.pdf |
| `iso_3166_1` | ISO 3166-1 Countries (with UN M.49 regional hierarchy) | 2023 | Global | ISO / UN Statistics Division | CC0 | https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes |
| `iso_3166_2` | ISO 3166-2 Country Subdivisions (states, provinces, regions) | 2023 | Global | ISO (via pycountry library) | LGPL (library); ISO data publicly available | https://pypi.org/project/pycountry/ |
| `un_m49` | UN M.49 Standard Country or Area Codes for Statistical Use | 2023 | Global | United Nations Statistics Division | Open | https://unstats.un.org/unsd/methodology/m49/overview |
| `hs_2022` | Harmonized Commodity Description and Coding System | 2022 | Global | World Customs Organization (via datasets/harmonized-system) | CC0 | https://github.com/datasets/harmonized-system |

---

## Crosswalk Edges

| Crosswalk | Source | License |
|-----------|--------|---------|
| NAICS 2022 / ISIC Rev 4 | UN Statistics Division concordance | Open |
| UN M.49 / ISO 3166-1 (~498 edges) | Derived from iso3166_all.csv (country-code + alpha-2 columns) | CC0 |
| HS 2022 / ISIC Rev 4 (~3,010 edges, broad) | World Bank WITS HS 2012->ISIC Rev 3 concordance, filtered to existing nodes | CC BY 4.0 |
| NACE Rev 2 / WZ 2008 (1:1) | Derived - WZ is a national adaptation of NACE | Open |
| NACE Rev 2 / ONACE 2008 (1:1) | Derived - ONACE is a national adaptation of NACE | Open |
| NACE Rev 2 / NOGA 2008 (1:1) | Derived - NOGA is a national adaptation of NACE | Open |

---

## Notes on Licensing

- **Public domain** systems (NAICS, SIC) may be used, modified, and redistributed freely with no attribution required, but attribution is given here for transparency.
- **Open** systems (ISIC, NACE, NIC, etc.) are freely available from their respective statistical agencies. Attribution is provided above.
- **CC BY 4.0** systems require attribution when redistributed. Attribution is provided above.
- The WorldOfTaxanomy codebase itself is MIT licensed. The data ingested from these sources remains under the original licenses.
- WorldOfTaxanomy does NOT redistribute raw classification data files. The ingesters download data directly from the authoritative sources at ingest time.

---

## Reporting a Licensing Issue

If you believe any system is being used in violation of its license, please open a GitHub issue immediately.
