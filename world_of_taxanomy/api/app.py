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
- NAICS 2022 (North America) \u2014 2,125 codes
- NIC 2008 (India) \u2014 2,070 codes
- SIC 1987 (USA/UK) \u2014 1,176 codes
- NACE Rev 2 (European Union) \u2014 996 codes
- WZ 2008 (Germany) \u2014 996 codes
- ONACE 2008 (Austria) \u2014 996 codes
- NOGA 2008 (Switzerland) \u2014 996 codes
- ANZSIC 2006 (Australia/NZ) \u2014 825 codes
- ISIC Rev 4 (Global/UN) \u2014 766 codes
- JSIC 2013 (Japan) \u2014 20 codes

## API
Base URL: https://worldoftaxanomy.com/api/v1

- GET /systems \u2014 List all classification systems
- GET /systems/{id} \u2014 Get system details with root codes
- GET /systems/{id}/nodes/{code} \u2014 Get a specific industry code
- GET /systems/{id}/nodes/{code}/children \u2014 Get child codes
- GET /systems/{id}/nodes/{code}/ancestors \u2014 Get parent chain
- GET /systems/{id}/nodes/{code}/equivalences \u2014 Get cross-system mappings
- GET /systems/{id}/nodes/{code}/translations \u2014 Translate to all other systems at once
- GET /systems/{id}/nodes/{code}/siblings \u2014 Sibling codes at the same hierarchy level
- GET /systems/{id}/nodes/{code}/subtree \u2014 Summary stats for all codes below this node
- GET /search?q={query} \u2014 Search across all systems
- GET /search?q={query}&grouped=true \u2014 Search results grouped by system
- GET /search?q={query}&context=true \u2014 Search with ancestor path and children for each match
- GET /compare?a={sys}&b={sys} \u2014 Side-by-side top-level sector comparison
- GET /diff?a={sys}&b={sys} \u2014 Codes in system A with no mapping to system B
- GET /nodes/{code} \u2014 Find all systems containing a code
- GET /systems/stats \u2014 Leaf and total node counts per system
- GET /systems?group_by=region \u2014 Systems grouped by geographic region
- GET /equivalences/stats \u2014 Crosswalk statistics
- GET /equivalences/stats?system_id={id} \u2014 Crosswalk stats filtered to one system

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
