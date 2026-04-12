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

WorldOfTaxanomy is a knowledge graph that connects 10 industry classification systems used around the world. It provides a REST API and MCP server for looking up, searching, and translating between classification codes.

## Systems
- NAICS 2022 (North America) - 2,125 codes
- NIC 2008 (India) - 2,070 codes
- SIC 1987 (USA/UK) - 1,176 codes
- NACE Rev 2 (European Union) - 996 codes
- WZ 2008 (Germany) - 996 codes
- ONACE 2008 (Austria) - 996 codes
- NOGA 2008 (Switzerland) - 996 codes
- ANZSIC 2006 (Australia/NZ) - 825 codes
- ISIC Rev 4 (Global/UN) - 766 codes
- JSIC 2013 (Japan) - 20 codes
- ISO 3166-1 Countries (Global) - 271 nodes (5 continents, 17 sub-regions, 249 countries)
- ISO 3166-2 Subdivisions (Global) - 5,246 nodes (200 country stubs + 5,046 subdivisions)
- UN M.49 Geographic Regions (Global) - 272 nodes (World, 5 regions, 24 sub-regions, 249 countries)
- HS 2022 Harmonized System (Global/WCO) - 6,960 nodes (21 sections, 97 chapters, 1,229 headings, 5,613 subheadings)
- CPC v2.1 Central Product Classification (Global/UN) - 4,596 nodes (10 sections, 71 divisions, 329 groups, 1,299 classes, 2,887 subclasses)

## Crosswalks
- CPC v2.1 / ISIC Rev 4 (~5,430 bidirectional edges, exact + partial)
- HS 2022 / CPC v2.1 (~11,686 bidirectional edges, exact + partial)

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

## Authentication
Register at https://worldoftaxanomy.com/register to get an API key.
Pass your key as: Authorization: Bearer wot_your_key_here

## MCP Server
Install: python -m world_of_taxanomy mcp
Transport: stdio
Tools: list_systems, get_industry, browse_children, get_ancestors, search_classifications, get_equivalences, translate_code, get_sector_overview
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
    app.include_router(auth_router.router)

    # Bot protection routes
    @app.get("/robots.txt", response_class=PlainTextResponse)
    async def robots_txt():
        return ROBOTS_TXT

    @app.get("/llms.txt", response_class=PlainTextResponse)
    async def llms_txt():
        return LLMS_TXT

    return app
