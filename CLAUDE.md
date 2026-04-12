# CLAUDE.md - WorldOfTaxanomy

## What this project is

WorldOfTaxanomy is a unified global industry classification knowledge graph. It connects 10 national/international classification systems as equal peers through equivalence mappings (crosswalk edges).

**20 systems, 110,484 codes, 49,450 crosswalk edges.**

| System | Region | Codes |
|--------|--------|-------|
| NAICS 2022 | North America | 2,125 |
| NIC 2008 | India | 2,070 |
| SIC 1987 | USA/UK | 1,176 |
| NACE Rev 2 | EU (27 countries) | 996 |
| WZ 2008 | Germany | 996 |
| ONACE 2008 | Austria | 996 |
| NOGA 2008 | Switzerland | 996 |
| ANZSIC 2006 | Australia/NZ | 825 |
| ISIC Rev 4 | Global (UN) | 766 |
| JSIC 2013 | Japan | 20 |
| ISO 3166-1 | Global | 271 |
| ISO 3166-2 | Global | 5,246 |
| UN M.49 | Global | 272 |
| HS 2022 | Global (WCO) | 6,960 |
| CPC v2.1 | Global (UN) | 4,596 |
| UNSPSC v24 | Global (GS1 US) | 77,337 |
| SOC 2018 | United States | 1,447 |
| ISCO-08 | Global (ILO) | 619 |
| CIP 2020 | United States | 2,848 |
| ISCED-F 2013 | Global (UNESCO) | 122 |

Three surfaces: **Web App** (Next.js), **REST API** (FastAPI), **MCP Server** (stdio).

## Architecture

```
WorldOfTaxanomy/
├── world_of_taxanomy/           # Python backend
│   ├── api/                     # FastAPI REST API
│   │   ├── app.py               # App factory with lifespan (pool management)
│   │   ├── deps.py              # DI: get_conn, get_current_user, validate_api_key
│   │   ├── schemas.py           # Pydantic models (system, node, auth, etc.)
│   │   ├── middleware.py        # Rate limiting (slowapi)
│   │   └── routers/
│   │       ├── systems.py       # GET /api/v1/systems, /api/v1/systems/{id}
│   │       ├── nodes.py         # GET .../nodes/{code}, /children, /ancestors
│   │       ├── search.py        # GET /api/v1/search?q=
│   │       ├── equivalences.py  # GET .../equivalences, /stats
│   │       └── auth.py          # POST register, login; GET /me; CRUD /keys
│   ├── mcp/                     # MCP server (stdio transport)
│   │   └── server.py
│   ├── ingest/                  # One ingester per classification system
│   │   ├── naics.py             # NAICS 2022 (Census Bureau CSV)
│   │   ├── isic.py              # ISIC Rev 4 (UN CSV)
│   │   ├── nace.py              # NACE Rev 2 (Eurostat XLSX)
│   │   ├── sic.py               # SIC 1987 (OSHA HTML + GitHub CSV fallback)
│   │   ├── anzsic.py            # ANZSIC 2006 (ABS XLS via xlrd)
│   │   ├── nic.py               # NIC 2008 (Indian govt PDF/CSV)
│   │   ├── jsic.py              # JSIC 2013 (skeleton: 20 divisions)
│   │   ├── nace_derived.py      # WZ 2008, ÖNACE 2008, NOGA 2008 (copy NACE nodes)
│   │   └── crosswalk.py         # ISIC↔NAICS concordance
│   ├── query.py                 # Core query functions (get_system, search, etc.)
│   ├── db.py                    # asyncpg pool (Neon PostgreSQL, statement_cache_size=0)
│   ├── schema.sql               # Core tables: classification_system, classification_node, equivalence
│   ├── schema_auth.sql          # Auth tables: app_user, api_key, usage_log
│   └── __main__.py              # CLI: serve, mcp, ingest, init-auth
├── frontend/                    # Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Home: Industry Map + Galaxy View
│       │   ├── explore/page.tsx # Full-text search with ?q= param support
│       │   ├── system/[id]/page.tsx # System detail with sectors + crosswalks
│       │   ├── dashboard/page.tsx   # Stats overview + crosswalk matrix
│       │   ├── layout.tsx       # Root layout (Geist fonts, Providers)
│       │   └── globals.css      # shadcn/ui theme tokens (oklch), dark + light
│       ├── components/
│       │   ├── IndustryMap.tsx   # 22 industry sectors with icons → /explore?q=
│       │   ├── ThemeToggle.tsx   # Dark/light mode toggle (next-themes)
│       │   ├── Providers.tsx     # ThemeProvider + React Query
│       │   ├── visualizations/GalaxyView.tsx  # D3.js force simulation, animated
│       │   ├── layout/Header.tsx # Nav with systems dropdown
│       │   ├── layout/Footer.tsx
│       │   └── ui/              # shadcn/ui components
│       └── lib/
│           ├── api.ts           # Typed API client (all endpoints)
│           ├── types.ts         # TypeScript interfaces matching Pydantic models
│           └── colors.ts        # System tint colors + sector colors
├── tests/                       # pytest suite (18 files)
│   ├── conftest.py              # test_wot schema isolation, seed data, session pool
│   ├── test_api_*.py            # API contract tests (systems, nodes, search, equivalences)
│   ├── test_auth.py             # hashing, JWT, registration, API keys, usage log
│   ├── test_node_detail_contract.py  # node detail page API contract
│   ├── test_mcp_*.py            # MCP protocol + tool handlers
│   ├── test_ingest_*.py         # per-system ingester tests
│   └── test_cli.py              # CLI argument parsing
├── .env                         # DATABASE_URL, JWT_SECRET (not committed)
└── requirements.txt             # asyncpg, fastapi, uvicorn, bcrypt, PyJWT, slowapi, etc.
```

## Tech stack

**Backend**: Python 3.9 · FastAPI · asyncpg · PostgreSQL on Neon (pgbouncer → `statement_cache_size=0`) · bcrypt · PyJWT · slowapi · MCP SDK

**Frontend**: Next.js 15 (App Router) · TypeScript · Tailwind CSS v4 · shadcn/ui · D3.js · React Query · next-themes · lucide-react

**Database**: Neon PostgreSQL. Three core tables (`classification_system`, `classification_node`, `equivalence`) plus three auth tables (`app_user`, `api_key`, `usage_log`).

## How to run

```bash
# Backend
source .env
python3 -m uvicorn world_of_taxanomy.api.app:create_app --factory --port 8000

# Frontend (requires Node.js - use nvm if npx not found)
cd frontend && npx next dev --port 3000
```

Frontend proxies `/api/*` to `:8000` via `next.config.ts` rewrites.

## How to test

```bash
# All tests (uses test_wot schema, never touches production)
python3 -m pytest tests/ -v

# Specific area
python3 -m pytest tests/test_auth.py -v
python3 -m pytest tests/test_ingest_naics.py -v
```

Test isolation: `conftest.py` creates a `test_wot` PostgreSQL schema, seeds NAICS/ISIC/SIC test data, and tears down after each test. Production data in `public` schema is never touched.

## Development practices

- **TDD - Red → Green → Refactor, strictly enforced**:
  1. **Red**: Write the test first. Run it. Confirm it fails for the right reason before writing any implementation code.
  2. **Green**: Write the minimum code to make the test pass. Nothing more.
  3. **Refactor**: Clean up implementation and tests while keeping all tests green.
  - Never write implementation before a failing test exists.
  - Never skip the "run it red" step - a test that was never red proves nothing.
  - Never refactor while tests are red.
- **No em-dashes**: Never use the em-dash character (U+2014) anywhere in the project - code, comments, docstrings, markdown, or configuration. Use a hyphen `-` instead. The CI pipeline enforces this with a grep check.
- **No speculative code**: Don't add features, abstractions, or error handling beyond what's asked.
- **Type safety**: All frontend code is TypeScript. All backend models are Pydantic. Keep types.ts in sync with schemas.py.
- **Theme support**: Both dark and light modes must work. Galaxy View text uses SVG shadow filters for contrast in both themes.
- **Test schema isolation**: Tests MUST use the `test_wot` schema. Never run test queries against `public`.

## Auth system

- Registration: POST `/api/v1/auth/register` → bcrypt password hash → JWT token
- Login: POST `/api/v1/auth/login` → JWT (15 min expiry)
- API keys: `wot_` + 32 hex chars, bcrypt-hashed, prefix-indexed
- Rate limits: anonymous 30 req/min, authenticated 1000 req/min
- JWT secret: `JWT_SECRET` env var (must be ≥32 chars in production)

## Key patterns

- **Lifespan handler** in `app.py` manages the asyncpg pool lifecycle
- **NACE-derived systems** (WZ, ÖNACE, NOGA) copy all NACE nodes and create 1:1 equivalence edges
- **Next.js API proxy**: client-side `api.ts` uses relative paths (`/api/v1/...`), `next.config.ts` rewrites them to the FastAPI backend
- **Galaxy View**: D3 force simulation in a React `useEffect`, with `useTheme()` for theme-aware rendering. Cleanup properly (stop simulation, cancel animation frame)
- **IndustryMap**: Links to `/explore?q=<term>`, Explore page reads `useSearchParams()` wrapped in `<Suspense>`

## What's NOT done yet

- ~~Node detail page~~ ✓ done - `/system/[id]/node/[code]/page.tsx` with breadcrumb, typographic depth, children panel, cross-system equivalences, inline API endpoint
- Auth frontend pages (login, register, API key dashboard) - backend is complete
- Production deployment (Vercel for frontend, Fly.io/Railway for backend)
- CI/CD pipeline
- Domain-specific taxonomy extensions (ICD codes, crop taxonomies, etc.)
