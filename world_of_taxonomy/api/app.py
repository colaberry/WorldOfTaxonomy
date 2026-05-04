"""FastAPI application factory."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import PlainTextResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from world_of_taxonomy.api.routers import systems, nodes, search, equivalences, explore
from world_of_taxonomy.api.routers import crosswalk_graph as crosswalk_graph_router
from world_of_taxonomy.api.routers import countries as countries_router
from world_of_taxonomy.api.routers import audit as audit_router
from world_of_taxonomy.api.routers import classify as classify_router
from world_of_taxonomy.api.routers import classify_demo as classify_demo_router
from world_of_taxonomy.api.routers import contact as contact_router
from world_of_taxonomy.api.routers import mcp_http as mcp_http_router
from world_of_taxonomy.api.routers import developers as developers_router
from world_of_taxonomy.api.routers import wiki as wiki_router
from world_of_taxonomy.api.routers import health as health_router
from world_of_taxonomy.api.middleware import (
    body_size_limit_middleware,
    limiter,
    rate_limit_middleware,
    request_id_middleware,
    request_logging_middleware,
    security_headers_middleware,
)
from world_of_taxonomy.api.metrics import (
    metrics_middleware,
    router as metrics_router,
)
from world_of_taxonomy.api.honeypot import router as honeypot_router
from world_of_taxonomy.api.csp_report import router as csp_report_router
from world_of_taxonomy.canary import router as canary_router
from world_of_taxonomy.db import get_pool
from world_of_taxonomy.wiki import build_llms_full_txt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database connection pool lifecycle.

    Graceful shutdown: uvicorn intercepts SIGTERM and stops accepting
    new connections, waits up to --timeout-graceful-shutdown seconds
    for in-flight requests to finish, then runs this shutdown half
    (after yield). We close the pool only after uvicorn has drained
    live requests, so no handler is cut mid-query.
    """
    app.state.pool = await get_pool()
    try:
        yield
    finally:
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

Sitemap: https://worldoftaxonomy.com/sitemap.xml
"""

LLMS_TXT = """\
# World Of Taxonomy

> Unified Global Classification Knowledge Graph
> 1,000+ systems, 1.2M+ nodes, 321K+ crosswalk edges.
> Open source (MIT). Data is informational only - use at your own risk.

World Of Taxonomy is a knowledge graph connecting 1,000+ classification systems across industry, geography, product/trade, occupational, education, health, financial, regulatory, and domain-specific vocabularies. It provides a REST API and MCP server for looking up, searching, translating, and classifying codes.

For the full reference, see: https://worldoftaxonomy.com/llms-full.txt

## Systems (1,000+ total, 1.2M+ nodes)

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
- UN M.49 Geographic Regions (Global) - 279 nodes

### Product / Trade
- HS 2022 Harmonized System (Global/WCO) - 6,961 nodes
- CPC v2.1 Central Product Classification (Global/UN) - 4,596 nodes
- UNSPSC v24 (Global/GS1 US) - 77,337 nodes

### Occupational
- ISCO-08 (Global/ILO) - 613 codes
- SOC 2018 (USA/BLS) - 1,447 codes
- ANZSCO 2022 (Australia/NZ) - 1,590 codes
- ESCO Occupations (EU) - 3,045 codes
- ESCO Skills (EU) - 14,247 codes
- O*NET-SOC (USA/DOL) - 867 codes

### Education
- ISCED 2011 (Global/UNESCO) - 20 codes
- ISCED-F 2013 (Global/UNESCO) - 122 codes
- CIP 2020 (USA/NCES) - 2,836 codes

### Health / Clinical
- ATC WHO 2021 (Global/WHO) - 6,440 codes
- ICD-11 MMS (Global/WHO) - 37,052 codes
- LOINC (Global/Regenstrief) - 102,751 codes

### Financial / Environmental / Regulatory
- COFOG (Global/UN) - 188 codes
- GICS Bridge (Global/MSCI/S&P) - 11 codes
- GHG Protocol (Global/WRI) - 20 codes
- CFR Title 49 (USA) - 104 codes
- FMCSA Regulations (USA) - 80 codes
- GDPR Articles (EU) - 110 codes
- ISO 31000 Risk Framework (Global) - 47 codes
- Patent CPC (Global/EPO/USPTO) - 254,249 codes

### Domain Deep-Dives (sector vocabularies linked to NAICS/ISIC nodes)
Truck Transportation: domain_truck_freight (44), domain_truck_vehicle (23), domain_truck_cargo (44), domain_truck_ops (27)
Agriculture: domain_ag_crop (48), domain_ag_livestock (27), domain_ag_method (29), domain_ag_grade (32)
Mining: domain_mining_mineral (25), domain_mining_method (21), domain_mining_reserve (12)
Utilities: domain_util_energy (17), domain_util_grid (15)
Construction: domain_const_trade (20), domain_const_building (18)
Cross-sector: domain_mfg_process (21), domain_retail_channel (19), domain_finance_instrument (25), domain_health_setting (24),
  domain_transport_mode (22), domain_info_media (21), domain_realestate_type (21), domain_food_service (23),
  domain_wholesale_channel (21), domain_prof_services (22), domain_education_type (22), domain_arts_content (23),
  domain_other_services (21), domain_public_admin (23), domain_supply_chain (24), domain_workforce_safety (24)

### Magna Compass Emerging Sectors
CORE gaps: domain_chemical_type (29), domain_defence_type (23), domain_water_env (28)
Emerging: domain_ai_data (25), domain_biotech (26), domain_space (24), domain_climate_tech (30),
  domain_adv_materials (27), domain_quantum (23), domain_digital_assets (25), domain_robotics (27),
  domain_energy_storage (25), domain_semiconductor (31), domain_synbio (28), domain_xr_meta (27)

## Crosswalks (58,647 edges total)
- ISIC Rev 4 / NAICS 2022 (bidirectional, ~3,418 edges)
- HS 2022 / CPC v2.1 (11,686 edges); CPC v2.1 / ISIC Rev 4 (5,430 edges)
- SOC 2018 / NAICS 2022 (55 edges); SOC 2018 / ISCO-08 (992 edges); ISCO-08 / ISIC Rev 4 (44 edges)
- CIP 2020 / SOC 2018 (5,903 edges); ISCED 2011 / ISCO-08 (25 edges); CIP 2020 / ISCED-F 2013 (1,615 edges)
- ESCO Occupations / ISCO-08 (6,048 edges); O*NET-SOC / SOC 2018 (1,734 edges)
- ANZSCO 2022 / ANZSIC 2006 (48 edges)
- CFR Title 49 / NAICS 2022 (437 edges)
- ISO 3166-1 / ISO 3166-2 / UN M.49 (geographic hierarchy, 698 edges)
- Nation-Sector Geographic Synergy: ISO 3166-1 countries / NAICS 2-digit sectors (98 edges, leadership/emerging)
- NAICS domain crosswalks: 484->truck, 11->agriculture, 21->mining, 22->utility, 23->construction (326 edges)

## API
Base URL: https://worldoftaxonomy.com/api/v1

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
Register at https://worldoftaxonomy.com/register to get an API key.
Pass your key as: Authorization: Bearer wot_your_key_here

## MCP Server
Install: python -m world_of_taxonomy mcp
Transport: stdio
Tools (21): list_systems, get_industry, browse_children, get_ancestors, search_classifications,
  get_equivalences, translate_code, get_sector_overview, compare_systems, diff_systems,
  get_node_by_code, get_crosswalk_stats, get_system_stats, get_subtree_summary,
  get_siblings, get_search_context, get_equivalences_for_system, get_country_taxonomy_profile,
  get_systems_for_country, list_crosswalks, get_grouped_search
"""


class EnvConfigError(RuntimeError):
    """Raised when required environment variables are missing or invalid."""


def _validate_env() -> None:
    """Fail fast on boot for missing or malformed env vars.

    Checked at app creation so container crashes immediately with a
    clear message instead of failing at the first DB query or auth
    request. Skipped when DISABLE_AUTH is truthy for local dev.
    """
    errors: list[str] = []

    if not os.getenv("DATABASE_URL", "").strip():
        errors.append("DATABASE_URL is required")

    disable_auth = os.getenv("DISABLE_AUTH", "").lower() in ("1", "true", "yes")
    if not disable_auth:
        secret = os.getenv("JWT_SECRET", "")
        if not secret:
            errors.append("JWT_SECRET is required when DISABLE_AUTH is not set")
        elif len(secret) < 32:
            errors.append(
                "JWT_SECRET must be at least 32 characters "
                f"(got {len(secret)}); generate one with "
                "python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )

    if errors:
        raise EnvConfigError(
            "Invalid environment configuration:\n  - " + "\n  - ".join(errors)
        )


def _scrub_event(event, hint):
    """Sentry before_send hook. Strips secrets from outgoing reports.

    Things we never want in Sentry:
      - dev_session cookie value (auth bypass if leaked)
      - Authorization header (API keys / JWTs)
      - Set-Cookie response headers
      - any header that looks like a secret name
    """
    request = event.get("request") if event else None
    if not request:
        return event

    headers = request.get("headers")
    if isinstance(headers, dict):
        for key in list(headers):
            low = key.lower()
            if low in ("authorization", "cookie", "set-cookie", "x-api-key"):
                headers[key] = "[scrubbed]"
            elif "secret" in low or "token" in low:
                headers[key] = "[scrubbed]"

    cookies = request.get("cookies")
    if isinstance(cookies, dict):
        if "dev_session" in cookies:
            cookies["dev_session"] = "[scrubbed]"

    return event


def _init_sentry() -> None:
    """Initialize Sentry only when SENTRY_DSN is set. Safe no-op otherwise.

    Uses the FastAPI / Starlette / asyncio auto-instrumentation that
    `sentry-sdk[fastapi]` ships, plus a before_send hook to scrub
    Authorization headers and the dev_session cookie before reports
    leave the process. Sample rates are tunable via env so prod can
    drop transaction tracing under load without redeploying.
    """
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            release=os.getenv("SENTRY_RELEASE") or os.getenv("CLOUD_RUN_REVISION") or None,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
            send_default_pii=False,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
            before_send=_scrub_event,
        )
    except Exception:
        # Never let telemetry wiring break startup.
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _validate_env()
    _init_sentry()

    # OpenAPI servers list. Lets /docs, /redoc, Scalar, and generated
    # SDKs target the production API by default instead of the relative
    # path of the page that loaded the spec. Override with
    # OPENAPI_SERVERS (comma-separated absolute URLs) when hosting a
    # preview or internal deployment.
    openapi_servers_env = os.getenv("OPENAPI_SERVERS", "").strip()
    if openapi_servers_env:
        openapi_servers = [
            {"url": u.strip()} for u in openapi_servers_env.split(",") if u.strip()
        ]
    else:
        openapi_servers = [
            {"url": "https://wot.aixcelerator.ai", "description": "Production"},
            {"url": "http://localhost:8000", "description": "Local development"},
        ]

    app = FastAPI(
        title="World Of Taxonomy",
        description=(
            "Unified global industry classification knowledge graph. "
            "Federation model connecting NAICS, ISIC, NACE, and more."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        servers=openapi_servers,
        lifespan=lifespan,
    )

    # CORS middleware. ALLOWED_ORIGINS is a comma-separated list of
    # absolute origins (scheme + host + optional port). Falls back to
    # localhost dev origins when unset.
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
    if allowed_origins_env:
        allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    else:
        allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip compression for responses > 500 bytes. Slashes bandwidth
    # for JSON listings, search results, and crosswalk payloads.
    app.add_middleware(GZipMiddleware, minimum_size=500)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.middleware("http")(rate_limit_middleware)

    # Prometheus instrumentation (counters + latency histogram).
    app.middleware("http")(metrics_middleware)

    # Security headers (applied to every response)
    app.middleware("http")(security_headers_middleware)

    # Structured access log (JSON line per request)
    app.middleware("http")(request_logging_middleware)

    # Request ID correlation (added last so it runs first on the way in,
    # making the id available to all downstream middleware + handlers).
    app.middleware("http")(request_id_middleware)

    # Body size cap (added after request_id so 413 responses still get
    # a correlation id; runs before the handler reads the body).
    app.middleware("http")(body_size_limit_middleware)

    # API routers
    app.include_router(explore.router)  # must be before systems (has /systems/stats)
    app.include_router(systems.router)
    app.include_router(nodes.router)
    app.include_router(search.router)
    app.include_router(equivalences.router)
    app.include_router(crosswalk_graph_router.router)
    app.include_router(countries_router.router)
    app.include_router(audit_router.router)
    app.include_router(classify_router.router)
    app.include_router(classify_demo_router.router)
    app.include_router(contact_router.router)
    app.include_router(mcp_http_router.router)
    app.include_router(developers_router.router)
    app.include_router(wiki_router.router)
    app.include_router(health_router.router)
    app.include_router(metrics_router)
    app.include_router(honeypot_router)
    app.include_router(csp_report_router)
    app.include_router(canary_router)

    # Bot protection routes
    @app.get("/robots.txt", response_class=PlainTextResponse)
    async def robots_txt():
        return ROBOTS_TXT

    @app.get("/llms.txt", response_class=PlainTextResponse)
    async def llms_txt():
        return LLMS_TXT

    @app.get("/llms-full.txt", response_class=PlainTextResponse)
    async def llms_full_txt():
        return build_llms_full_txt()

    return app
