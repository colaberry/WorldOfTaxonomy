"""Country taxonomy profile API router.

GET /api/v1/countries/stats    - bulk stats for all countries (world map)
GET /api/v1/countries/{code}   - full taxonomy profile for a country
"""
from fastapi import APIRouter, HTTPException

from world_of_taxanomy.api.deps import get_conn
from world_of_taxanomy.query.browse import (
    get_country_sector_strengths,
    get_systems_for_country,
)

from fastapi import Depends

router = APIRouter(prefix="/api/v1/countries", tags=["countries"])


@router.get("/stats")
async def get_countries_stats(conn=Depends(get_conn)):
    """Return per-country taxonomy coverage stats for all countries.

    Used by the world map visualization on the home page.
    Returns a list of country objects with:
    - country_code: ISO 3166-1 alpha-2
    - system_count: number of applicable classification systems
    - has_official: whether the country has its own official national standard
    - sector_strength_count: number of sector strengths from the geo-sector crosswalk
    """
    rows = await conn.fetch(
        """SELECT
             csl.country_code,
             COUNT(DISTINCT csl.system_id) AS system_count,
             COUNT(DISTINCT CASE
               WHEN csl.relevance IN ('official', 'regional', 'historical')
               THEN csl.system_id END) AS country_specific_count,
             BOOL_OR(csl.relevance = 'official') AS has_official,
             COALESCE(ss.strength_count, 0) AS sector_strength_count,
             (
               SELECT csl2.system_id
               FROM country_system_link csl2
               WHERE csl2.country_code = csl.country_code
                 AND csl2.relevance IN ('official', 'regional', 'historical')
               ORDER BY CASE csl2.relevance
                 WHEN 'official'     THEN 1
                 WHEN 'regional'     THEN 2
                 WHEN 'historical'   THEN 3
               END
               LIMIT 1
             ) AS primary_system_id
           FROM country_system_link csl
           LEFT JOIN (
             SELECT source_code AS country_code, COUNT(*) AS strength_count
             FROM equivalence
             WHERE source_system = 'iso_3166_1'
               AND target_system = 'naics_2022'
             GROUP BY source_code
           ) ss ON ss.country_code = csl.country_code
           GROUP BY csl.country_code, ss.strength_count
           ORDER BY csl.country_code"""
    )
    return [dict(r) for r in rows]


@router.get("/{country_code}")
async def get_country_profile(
    country_code: str,
    conn=Depends(get_conn),
):
    """Return taxonomy profile for a country.

    Includes:
    - Country metadata (from iso_3166_1 if ingested)
    - Applicable classification systems ordered by relevance
      (official national system, regional bloc system, UN recommended, historical)
    - Known sector strengths (from the geo-sector crosswalk)

    country_code: ISO 3166-1 alpha-2 code (e.g. DE, PK, MX, ID, US)
    """
    code = country_code.upper()
    if len(code) != 2 or not code.isalpha():
        raise HTTPException(status_code=400, detail="country_code must be a 2-letter ISO 3166-1 alpha-2 code")

    # Country metadata from iso_3166_1 (best-effort - may not be present if not ingested)
    country_row = await conn.fetchrow(
        """SELECT code, title, parent_code
           FROM classification_node
           WHERE system_id = 'iso_3166_1' AND code = $1""",
        code,
    )

    # Applicable classification systems
    systems = await get_systems_for_country(conn, code)

    if not systems and country_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for country code '{code}'. "
                   "Ensure iso_3166_1 and crosswalk_country_system have been ingested.",
        )

    # Sector strengths from geo-sector crosswalk
    sector_strengths = await get_country_sector_strengths(conn, code)

    country_info = {
        "code": code,
        "title": country_row["title"] if country_row else None,
        "parent_region": country_row["parent_code"] if country_row else None,
    }

    return {
        "country": country_info,
        "classification_systems": systems,
        "sector_strengths": sector_strengths,
    }
