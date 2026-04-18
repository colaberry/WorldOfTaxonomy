# Rebuild Checklist

Ordered, executable steps to stand up WorldOfTaxonomy from a clean checkout on a new machine. Assumes macOS/Linux, Python 3.11, Node 20+, Postgres access (Neon recommended).

Read [HANDOVER.md](../../HANDOVER.md) first for context.

---

## 0. Prerequisites

- Python 3.11 (`python3 --version`).
- Node 20 or later via `nvm` (`nvm install 20 && nvm use 20`).
- A Postgres database. For prod-like behavior, use Neon (pgbouncer present). For local dev, any Postgres works.
- Optional: Docker + docker-compose if you want the [docker-compose.yml](../../docker-compose.yml) stack.

---

## 1. Clone and provision env

```bash
git clone <repo-url> WorldOfTaxonomy
cd WorldOfTaxonomy
cp .env.example .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
# Optional
ANTHROPIC_API_KEY=sk-ant-...
REPORT_EMAIL=you@example.com
```

For local dev you may also set `DISABLE_AUTH=true` to skip JWT validation entirely. Never do this in production.

---

## 2. Install Python deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Initialize the database

```bash
source .env
python -m world_of_taxonomy init         # core schema (classification_system, classification_node, equivalence, ...)
python -m world_of_taxonomy init-auth    # auth schema (app_user, api_key, usage_log, daily_usage)
```

Verify:

```bash
psql "$DATABASE_URL" -c "\dt"
```

You should see both sets of tables.

---

## 4. Ingest anchor systems first

The 860+ non-anchor systems reference NAICS, ISIC, and NACE. Load those first so their crosswalks resolve.

```bash
python -m world_of_taxonomy ingest naics
python -m world_of_taxonomy ingest isic
python -m world_of_taxonomy ingest nace
python -m world_of_taxonomy ingest isic_naics_crosswalk
```

Smoke test:

```bash
python -m world_of_taxonomy stats
python -m world_of_taxonomy browse naics_2022 54
python -m world_of_taxonomy search "software"
python -m world_of_taxonomy equiv naics_2022 541511
```

---

## 5. Ingest the rest (optional at first)

Full catalog (slow; downloads many upstream sources):

```bash
python -m world_of_taxonomy ingest all
python -m world_of_taxonomy ingest all-crosswalks
python -m world_of_taxonomy ingest all-domains
```

Or pick targets one at a time. Each ingester is idempotent (it upserts by `system_id` + `code`). The list of targets is in [world_of_taxonomy/__main__.py](../../world_of_taxonomy/__main__.py). Upstream attribution for each system: [DATA_SOURCES.md](../../DATA_SOURCES.md).

---

## 6. Run the REST API

```bash
python -m uvicorn world_of_taxonomy.api.app:create_app --factory --port 8000
```

Smoke test in another shell:

```bash
curl http://localhost:8000/api/v1/systems | head -c 400
curl "http://localhost:8000/api/v1/search?q=hospital" | head -c 400
curl http://localhost:8000/api/v1/equivalences/stats | head -c 400
```

---

## 7. Run the MCP server

```bash
python -m world_of_taxonomy mcp
```

Point Claude Desktop at it via `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "worldoftaxonomy": {
      "command": "/absolute/path/to/run_mcp.sh"
    }
  }
}
```

Restart Claude Desktop. Ask: "Use the WorldOfTaxonomy MCP to translate NAICS 541511 to ISIC Rev 4." You should see a `translate_code` tool call.

---

## 8. Export static assets for the frontend

```bash
python scripts/export_crosswalk_data.py   # crosswalk-data/pair__*.json + all-sections.json
python scripts/export_tree_data.py        # tree-data/<system_id>.json
python scripts/build_llms_txt.py          # frontend/public/llms-full.txt
```

Run these whenever the underlying data or wiki content changes. CI does NOT auto-regenerate; committers are responsible.

---

## 9. Run the frontend

```bash
cd frontend
npm ci
npm run dev    # http://localhost:3000
```

`predev` hook copies `wiki/`, `blog/`, `crosswalk-data/`, `tree-data/` into `src/content/` first. The app proxies `/api/v1/*` to `http://localhost:8000` via `next.config.ts`.

Smoke test in a browser:

1. `/` - galaxy renders with 1000+ system nodes animating into place.
2. `/explore` - stats cards + systems table visible; typing a query flips to search results.
3. `/system/naics_2022` - hierarchy tree loads; clicking a code navigates to `/system/naics_2022/node/<code>`.
4. `/crosswalk-explorer` - Cytoscape graph loads on demand.
5. `/guide` - all 10 wiki pages list and open.
6. Theme toggle flips dark <-> light with no flash.

---

## 10. Tests green

```bash
# backend
python3 -m pytest tests/ -v

# frontend
cd frontend && npx tsc --noEmit && npm run build
```

Both must be clean. Also check:

```bash
grep -rn $'\xe2\x80\x94' world_of_taxonomy/ tests/ frontend/src/ *.md docs/ && echo "EM-DASH FOUND" || echo "clean"
```

This is the same grep CI runs. Must return `clean`.

---

## 11. Deploy

### Frontend (Vercel)

1. Connect the GitHub repo in Vercel.
2. Project root: `frontend`.
3. Build command: `npm run build` (the `prebuild` hook runs automatically).
4. Env vars: `BACKEND_URL=https://<your-api-host>`, `REVALIDATE_SECRET=<random>`.
5. Custom domain: point `worldoftaxonomy.com` at the Vercel deployment.

### Backend + MCP

1. Build container from [Dockerfile.backend](../../Dockerfile.backend).
2. Deploy anywhere that accepts a container (Fly, Railway, Cloud Run, Fargate, your own VPS).
3. Entry: `uvicorn world_of_taxonomy.api.app:create_app --factory --host 0.0.0.0 --port 8000`.
4. Env vars from step 1.
5. DNS: `wot.aixcelerator.app` (or your own API host) -> container.
6. CORS allow-list: add your frontend origin in [world_of_taxonomy/api/middleware.py](../../world_of_taxonomy/api/middleware.py).

### Database

- Neon: create a project, copy the pooled connection string, set as `DATABASE_URL`.
- Remember: asyncpg pool needs `statement_cache_size=0` on pgbouncer-fronted Postgres. Production code path in [world_of_taxonomy/db.py](../../world_of_taxonomy/db.py) should set this explicitly when `DATABASE_URL` contains `pooler`.

### OAuth providers

Follow [OAUTH_PRODUCTION_SETUP.md](../../OAUTH_PRODUCTION_SETUP.md) for GitHub, Google, and LinkedIn redirect URIs per environment.

---

## 12. Post-deploy verification

- `GET https://<api-host>/api/v1/systems` returns JSON.
- `GET https://<frontend-host>/llms-full.txt` returns the full wiki as plain text.
- MCP client (Claude Desktop) connects and lists 23 tools.
- A logged-out user hits the anonymous rate cap (30/min) with rapid curls.
- Sign up via OAuth; API key creation works from the account dashboard (when the auth frontend ships).

---

## 13. Ongoing maintenance

- **Adding a system**: TDD. Red test first. 7-step recipe in [CONTRIBUTING.md](../../CONTRIBUTING.md), long-form in [docs/adding-a-new-system.md](../adding-a-new-system.md).
- **Updating wiki**: edit `wiki/*.md`, then `python scripts/build_llms_txt.py`, then commit both.
- **Updating crosswalks**: rerun the relevant ingester, then `python scripts/export_crosswalk_data.py`, commit the updated JSON.
- **Bumping node counts in [CLAUDE.md](../../CLAUDE.md)**: do not hand-edit; the numbers should come from `python -m world_of_taxonomy stats`.

---

## 14. What to skip on first rebuild

You do not need all of these to have a working system:

- Full 864-ingester run. NAICS + ISIC + NACE is enough to demo the API, MCP, and web app. Layer in more systems as needed.
- AI classify endpoint. It needs `ANTHROPIC_API_KEY` and Pro+ auth. Skip if unused.
- OAuth providers. Password login works without them.
- Vercel. `npm run build && npm start` on any host works.
- llms-full.txt. Nice to have for AI crawlers; not required for humans.

Everything else is required.
