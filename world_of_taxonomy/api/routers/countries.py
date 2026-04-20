"""Country taxonomy profile API router.

GET /api/v1/countries/stats    - bulk stats for all countries (world map)
GET /api/v1/countries/{code}   - full taxonomy profile for a country
"""
from fastapi import APIRouter, HTTPException

from world_of_taxonomy.api.deps import get_conn
from world_of_taxonomy.query.browse import (
    get_country_sector_strengths,
    get_systems_for_country,
)

from fastapi import Depends

router = APIRouter(prefix="/api/v1/countries", tags=["countries"])


@router.get("")
async def list_countries(conn=Depends(get_conn)):
    """Return countries that have at least one applicable classification system.

    Used by the frontend country-filter dropdown. Sorted alphabetically by
    country title (from iso_3166_1). Countries whose ISO 3166-1 node has not
    been ingested are excluded so the dropdown never shows bare codes.
    """
    rows = await conn.fetch(
        """SELECT csl.country_code AS code,
                  n.title,
                  COUNT(DISTINCT csl.system_id) AS system_count,
                  BOOL_OR(csl.relevance = 'official') AS has_official
             FROM country_system_link csl
             JOIN classification_node n
               ON n.system_id = 'iso_3166_1' AND n.code = csl.country_code
            GROUP BY csl.country_code, n.title
            ORDER BY n.title"""
    )
    return [dict(r) for r in rows]


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
               ORDER BY
                 -- Industry classification systems take precedence over
                 -- occupational/regulatory/other official systems for map coloring
                 CASE WHEN csl2.system_id IN (
                   'naics_2022','nace_rev2','wz_2008','onace_2008','noga_2008',
                   'anzsic_2006','nic_2008','jsic_2013','cnae_2012','csic_2017',
                   'gbt_4754','okved_2','kbli_2020','scian_2018','sic_sa',
                   'ateco_2007','naf_rev2','pkd_2007','sbi_2008','sni_2007',
                   'db07','tol_2008','cae_rev3','cz_nace','teaor_2008',
                   'caen_rev2','nkd_2007','sk_nace','nkid','emtak',
                   'nace_lt','nk_lv','nace_tr',
                   'ciiu_co','ciiu_ar','ciiu_cl','ciiu_pe','ciiu_ec',
                   'caeb','ciiu_ve','ciiu_cr','ciiu_gt','ciiu_pa',
                   'vsic_2018','bsic','psic_pk','ksic_2017','ssic_2020',
                   'msic_2008','tsic_2009','psic_2009',
                   'isic_ng','isic_ke','isic_eg','isic_sa','isic_ae',
                   'isic_rev4'
                 ) THEN 0 ELSE 1 END,
                 CASE csl2.relevance
                   WHEN 'official'   THEN 1
                   WHEN 'regional'   THEN 2
                   WHEN 'historical' THEN 3
                 END,
                 csl2.system_id
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
