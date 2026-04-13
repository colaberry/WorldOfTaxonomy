"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from world_of_taxanomy.api.routers import systems, nodes, search, equivalences, explore
from world_of_taxanomy.api.routers import auth as auth_router
from world_of_taxanomy.api.routers import countries as countries_router
from world_of_taxanomy.api.middleware import limiter, rate_limit_middleware
from world_of_taxanomy.db import get_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection pool lifecycle."""
    app.state.pool = await get_pool()
    yield
    await app.state.pool.close()


ROBOTS_TXT = """\
User-agent: *
Allow: /
Crawl-delay: 2

User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: AhrefsBot
Disallow: /api/

User-agent: SemrushBot
Disallow: /api/

User-agent: MJ12bot
Disallow: /api/

Sitemap: https://worldoftaxanomy.com/sitemap.xml
"""

LLMS_TXT = """\
# WorldOfTaxanomy

> Unified Global Industry Classification Knowledge Graph

WorldOfTaxanomy is a knowledge graph connecting 88 classification systems across industry, geography, product/trade, occupational, education, health, financial, regulatory, and domain-specific vocabularies. It provides a REST API and MCP server for looking up, searching, and translating between classification codes.

## Systems (88 total)

### Industry Classification Standards
- NAICS 2022 (North America) - 2,125 codes
- ISIC Rev 4 (Global/UN) - 766 codes
- NACE Rev 2 (European Union) - 996 codes
- SIC 1987 (USA/UK) - 1,176 codes
- NIC 2008 (India) - 2,070 codes
- WZ 2008 (Germany) / ONACE 2008 (Austria) / NOGA 2008 (Switzerland) - 996 codes each
- ANZSIC 2006 (Australia/NZ) - 825 codes
- JSIC 2013 (Japan) - 20 codes

### Geographic
- ISO 3166-1 Countries (Global) - 271 nodes
- ISO 3166-2 Subdivisions (Global) - 5,246 nodes
- UN M.49 Geographic Regions (Global) - 272 nodes

### Product / Trade
- HS 2022 Harmonized System (Global/WCO) - 6,960 nodes
- CPC v2.1 Central Product Classification (Global/UN) - 4,596 nodes
- UNSPSC v24 (Global/GS1 US) - 77,337 nodes

### Occupational
- ISCO-08 (Global/ILO) - 619 codes
- SOC 2018 (USA/BLS) - 1,447 codes
- ANZSCO 2022 (Australia/NZ) - ~1,590 codes
- ESCO Occupations (EU) - ~2,942 codes
- ESCO Skills (EU) - ~13,890 codes
- O*NET-SOC (USA/DOL) - ~867 codes

### Education
- ISCED 2011 (Global/UNESCO) - 20 codes
- ISCED-F 2013 (Global/UNESCO) - 122 codes
- CIP 2020 (USA/NCES) - 2,848 codes

### Health / Clinical
- ATC WHO 2021 (Global/WHO) - 6,440 codes
- ICD-11 MMS (Global/WHO) - 37,052 codes
- LOINC (Global/Regenstrief) - ~102,751 codes

### Financial / Environmental / Regulatory
- COFOG (Global/UN) - 188 codes
- GICS Bridge (Global/MSCI/S&P) - 11 codes
- GHG Protocol (Global/WRI) - 20 codes
- CFR Title 49 (USA) - 104 codes
- FMCSA Regulations (USA) - 80 codes
- GDPR Articles (EU) - 110 codes
- ISO 31000 Risk Framework (Global) - 47 codes
- Patent CPC (Global/EPO/USPTO) - ~260,000 codes

### Domain Deep-Dives (sector vocabularies linked to NAICS/ISIC nodes)
Truck Transportation: domain_truck_freight (44), domain_truck_vehicle (23), domain_truck_cargo (46), domain_truck_ops (27)
Agriculture: domain_ag_crop (46), domain_ag_livestock (27), domain_ag_method (28), domain_ag_grade (30)
Mining: domain_mining_mineral (25), domain_mining_method (20), domain_mining_reserve (12)
Utilities: domain_util_energy (17), domain_util_grid (15)
Construction: domain_const_trade (20), domain_const_building (17)
Cross-sector: domain_mfg_process, domain_retail_channel, domain_finance_instrument, domain_health_setting,
  domain_transport_mode, domain_info_media, domain_realestate_type, domain_food_service,
  domain_wholesale_channel, domain_prof_services, domain_education_type, domain_arts_content,
  domain_other_services, domain_public_admin, domain_supply_chain, domain_workforce_safety

### Magna Compass Emerging Sectors
CORE gaps: domain_chemical_type (29), domain_defence_type (23), domain_water_env (28)
Emerging: domain_ai_data (25), domain_biotech (26), domain_space (24), domain_climate_tech (30),
  domain_adv_materials (27), domain_quantum (23), domain_digital_assets (25), domain_robotics (27),
  domain_energy_storage (25), domain_semiconductor (31), domain_synbio (28), domain_xr_meta (27)

## Crosswalks (~57,760 edges total)
- ISIC Rev 4 / NAICS 2022 (bidirectional, ~2,000 edges)
- HS 2022 / CPC v2.1 (~11,686 edges); CPC v2.1 / ISIC Rev 4 (~5,430 edges)
- SOC 2018 / NAICS 2022 (~2,000 edges); SOC 2018 / ISCO-08 (~500 edges); ISCO-08 / ISIC Rev 4 (~500 edges)
- CIP 2020 / SOC 2018 (~2,000 edges); ISCED 2011 / ISCO-08 (~25 edges); CIP 2020 / ISCED-F 2013 (~2,000 edges)
- ESCO Occupations / ISCO-08 (~3,000 edges); O*NET-SOC / SOC 2018 (~867 edges)
- ANZSCO 2022 / ANZSIC 2006 (~1,590 edges)
- CFR Title 49 / NAICS 2022 (~300 edges)
- ISO 3166-1 / ISO 3166-2 / UN M.49 (geographic hierarchy)
- Nation-Sector Geographic Synergy: ISO 3166-1 countries / NAICS 2-digit sectors (98 edges, leadership/emerging)
- NAICS domain crosswalks: 484->truck, 11->agriculture, 21->mining, 22->utility, 23->construction (~326 edges)

## API
Base URL: https://worldoftaxanomy.com/api/v1

- GET /systems - List all classification systems
- GET /systems/{id} - Get system details with root codes
- GET /systems/{id}/nodes/{code} - Get a specific industry code
- GET /systems/{id}/nodes/{code}/children - Get child codes
- GET /systems/{id}/nodes/{code}/ancestors - Get parent chain
- GET /systems/{id}/nodes/{code}/equivalences - Get cross-system mappings
- GET /systems/{id}/nodes/{code}/translations - Translate to all other systems at once
- GET /systems/{id}/nodes/{code}/siblings - Sibling codes at the same hierarchy level
- GET /systems/{id}/nodes/{code}/subtree - Summary stats for all codes below this node
- GET /search?q={query} - Search across all systems
- GET /search?q={query}&grouped=true - Search results grouped by system
- GET /search?q={query}&context=true - Search with ancestor path and children for each match
- GET /compare?a={sys}&b={sys} - Side-by-side top-level sector comparison
- GET /diff?a={sys}&b={sys} - Codes in system A with no mapping to system B
- GET /nodes/{code} - Find all systems containing a code
- GET /systems/stats - Leaf and total node counts per system
- GET /systems?group_by=region - Systems grouped by geographic region
- GET /equivalences/stats - Crosswalk statistics
- GET /equivalences/stats?system_id={id} - Crosswalk stats filtered to one system
- GET /systems?country={code} - Systems applicable to a country (e.g. DE, PK, US)
- GET /countries/stats - Per-country taxonomy coverage stats (for world map)
- GET /countries/{code} - Full taxonomy profile for a country (systems + sector strengths)

## Authentication
Register at https://worldoftaxanomy.com/register to get an API key.
Pass your key as: Authorization: Bearer wot_your_key_here

## MCP Server
Install: python -m world_of_taxanomy mcp
Transport: stdio
Tools (21): list_systems, get_industry, browse_children, get_ancestors, search_classifications,
  get_equivalences, translate_code, get_sector_overview, compare_systems, diff_systems,
  get_node_by_code, get_crosswalk_stats, get_system_stats, get_subtree_summary,
  get_siblings, get_search_context, get_equivalences_for_system, get_country_taxonomy_profile,
  get_systems_for_country, list_crosswalks, get_grouped_search
"""


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="WorldOfTaxanomy",
        description=(
            "Unified global industry classification knowledge graph. "
            "Federation model connecting NAICS, ISIC, NACE, and more."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.middleware("http")(rate_limit_middleware)

    # API routers
    app.include_router(explore.router)  # must be before systems (has /systems/stats)
    app.include_router(systems.router)
    app.include_router(nodes.router)
    app.include_router(search.router)
    app.include_router(equivalences.router)
    app.include_router(countries_router.router)
    app.include_router(auth_router.router)

    # Bot protection routes
    @app.get("/robots.txt", response_class=PlainTextResponse)
    async def robots_txt():
        return ROBOTS_TXT

    @app.get("/llms.txt", response_class=PlainTextResponse)
    async def llms_txt():
        return LLMS_TXT

    return app
