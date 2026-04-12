# Data Sources

This directory holds downloaded classification data files. Files are auto-downloaded by the ingestion pipeline and gitignored.

## Sources

| System | Source | URL |
|--------|--------|-----|
| NAICS 2022 | U.S. Census Bureau | https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx |
| ISIC Rev 4 | United Nations Statistics Division | https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_english_structure.Txt |
| Crosswalk | U.S. Census Bureau | https://www.census.gov/naics/concordances/2022_NAICS_to_ISIC_Rev_4.xlsx |
| ISO 3166-1 Countries | lukes/ISO-3166-Countries-with-Regional-Codes (CC0) | https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv |
| ISO 3166-2 Subdivisions | pycountry library (no file download - uses pycountry in-memory) | pip install pycountry |
| UN M.49 Geographic Regions | lukes/ISO-3166-Countries-with-Regional-Codes (reuses iso3166_all.csv, CC0) | https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv |

## Re-downloading

```bash
# Delete cached files and re-ingest
rm -rf data/naics/ data/isic/ data/crosswalk/
python -m world_of_taxanomy ingest all
```
