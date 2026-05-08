# Geographic Classification

> **TL;DR:** WoT hosts 11 geographic classification systems anchoring the spatial axis: country codes (ISO 3166-1, UN M.49), subdivision codes (ISO 3166-2, EU NUTS 2021, US FIPS), feature classification (GeoNames Features), airport codes (ICAO Airport), climate zones (Köppen), and country development / income groupings (WB Income Groups, ADB Sector). Distinct from the country-link layer that maps a country to its applicable taxonomies — this page is the geography-as-classification view.

---

## Country and territory codes

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `iso_3166_1` | 271 | ISO | Country / dependency / autonomous-region two-letter, three-letter, numeric codes |
| `un_m49` | 279 | UN Statistics Division | UN M.49 standard country / area / region codes (with regional groupings: SDG regions, geographic regions) |

ISO 3166-1 is the operational country code (US, GB, DE, etc.); UN M.49 layers in regional and sub-regional groupings (Northern America, Western Europe, Sub-Saharan Africa). Use both: ISO 3166-1 for the country, M.49 for any aggregation.

## Subdivision codes

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `iso_3166_2` | 5,246 | ISO | First-order country subdivisions globally (US states, German Bundesländer, French régions, etc.) |
| `eu_nuts_2021` | 124 | Eurostat | Nomenclature of Territorial Units for Statistics (NUTS 1/2/3) |
| `us_fips` | 86 | NIST (US) | Federal Information Processing Standards geographic codes (states + outlying areas) |
| `nuts_candidate` | 11 | Eurostat | NUTS candidate codes for prospective EU members and candidates |

ISO 3166-2 is the universal subdivision code; NUTS is the EU-specific statistical hierarchy (NUTS 1 -> 2 -> 3); FIPS is the US legacy that many federal datasets still cite alongside ISO 3166-2.

## Feature and place classification

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `geonames_features` | 693 | GeoNames | Feature codes for places (administrative, hydrographic, populated, terrain, undersea, vegetation, spots/buildings/farms, roads/railroads) |
| `icao_airport` | 21 | ICAO | ICAO airport-code regional groupings (KXXX = US contiguous, EXXX = Europe, etc.) |

GeoNames is the "what kind of place is this" classifier (a city, a river, a mountain, an administrative division). Use it alongside ISO 3166-2 to anchor a place: "Boston is `P.PPLA` (seat of first-order admin division) within `US-MA`."

## Climate as geography

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `koppen_climate` | 17 | Köppen-Geiger | Climate-zone classification (A tropical, B arid, C temperate, D continental, E polar, with subdivisions) |

Climate zones are not a coordinate but they classify *where* an observation can apply (a tropical zone Af city has different agricultural / disease / energy profiles than a desert BWh city).

## Country groupings (development and macroeconomic)

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `wb_income` | 27 | World Bank | Country income classification (low / lower-middle / upper-middle / high; updated annually) |
| `adb_sector` | 46 | ADB | Asian Development Bank sector taxonomy with country-region context |

These are referenced from [Financial Systems](./financial-systems.md) as well — relevant when development-finance or DFI activity is being classified.

## Decision tree

| What you are doing | Use |
|---|---|
| Tagging a country | `iso_3166_1` (always; the operational anchor) |
| Aggregating to a region | `un_m49` (SDG regions, geographic regions) |
| Tagging a state / province / region | `iso_3166_2` (universal) or `us_fips` / `eu_nuts_2021` (jurisdiction-specific) |
| Anchoring a statistical region in EU | `eu_nuts_2021` (the EU statistics convention) |
| Classifying *what kind* of place it is | `geonames_features` (city / river / mountain / etc.) |
| Anchoring an airport | `icao_airport` (regional grouping); use IATA codes for the specific airport (out of scope here) |
| Climate-zone tagging | `koppen_climate` |
| Development-finance country tier | `wb_income` |

## Crosswalk navigation

```bash
# Translate an ISO 3166-2 subdivision to NUTS
GET /api/v1/systems/iso_3166_2/nodes/FR-IDF/translations

# Find the GeoNames feature class for a populated place
GET /api/v1/systems/geonames_features/nodes/P.PPLC

# Country profile (uses iso_3166_1 codes)
GET /api/v1/countries/US
```

## What WoT does not host

- **Postal codes** (ZIP, postcode) - operational data, grows continuously, fails the "stable enumeration" test in the inclusion policy.
- **Specific airport / port / station identifiers** (IATA, IMO, UN/LOCODE) - operational registries, ~tens of thousands of entries each. Candidates for "World of Registries" sister product, not WoT.
- **Latitude/longitude coordinate systems** - notations, not classifications.
- **Cadastral parcel IDs** - jurisdiction-specific operational data.

## Related reading

- [Inclusion Policy](./inclusion-policy.md) - why postal codes and IATA are not in WoT.
- [Crosswalk Map](./crosswalk-map.md) - geography is a frequent join axis.
