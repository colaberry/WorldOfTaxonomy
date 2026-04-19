# WorldOfTaxonomy - Roadmap

Current state: **1,000+ systems, 1,212,173+ codes, ~326,000 crosswalk edges, 249 countries profiled.**

---

## Now - developer experience and launch readiness

- [ ] **Hosted public API**
  A free public endpoint so developers can try the API without self-hosting.
  Primary blocker for adoption. Target: `api.worldoftaxonomy.com` with 30 req/min
  anonymous tier and 1,000 req/min authenticated tier.

- [ ] **API key dashboard (frontend UI)**
  Backend auth is complete. Users need a UI to create/revoke API keys.
  Pages: key list, create key, revoke key, usage stats.

- [ ] **Production DB ingestion**
  Run `ingest all` against the production database so the hosted API
  and world map reflect all 1,000+ systems.

- [ ] **Docker image on Docker Hub / GitHub Container Registry**
  `docker pull ghcr.io/colaberry/worldoftaxonomy:latest`
  Removes the need to build locally for self-hosting.

---

## Short-term - data completeness

- [ ] **Remaining EU NACE national adaptations**
  Target: all 27 EU member states. Currently missing: GR, MT, LU, CY, IE.

- [ ] **Additional ISIC national adaptations**
  Central Asia (KZ, UZ), West Africa (GH, SN, CM),
  South Asia (MM, NP, LK).

- [ ] **SITC-NAICS crosswalk**
  Map UN SITC Rev 4 product codes to NAICS economic activity codes.

---

## Medium-term - developer ecosystem

- [ ] **Python client library** (`pip install world-of-taxonomy-client`)
- [ ] **JavaScript / TypeScript client** (`npm install world-of-taxonomy-client`)
- [ ] **Bulk export: Hugging Face Datasets** - monthly Parquet snapshots
- [ ] **dbt package** - warehouse-native crosswalk join macros
- [ ] **Email digest** for contributors on new system additions

---

## Long-term - knowledge graph intelligence

- [ ] **Semantic similarity crosswalk** - embedding-based suggested equivalences
- [ ] **Change tracking** - detect when system editions change, flag broken crosswalk edges
- [ ] **GraphQL API** - traversal-style queries as an alternative to REST
- [ ] **Embedded SQLite snapshot** - for air-gapped / mobile use
- [ ] **Taxonomy authoring UI** - contribute systems without touching code

---

## Community asks (domain expertise needed)

- Healthcare: SNOMED CT mapping to ICD-11
- Legal: EU ELI / ECLI legal act classifications
- Agriculture: FAO commodity codes and AGROVOC
- Finance: LEI entity -> GICS sector mapping
- Environment: CBD habitat classifications

---

## Previously completed

- [x] **Domain crosswalk integration (sector-anchor bridges + edge_kind labeling)**
  Bridged all 434 curated domain taxonomies to NAICS 2022 via sector-anchor
  rules, plus ISIC Rev 4 / NACE Rev 2 fan-out for each sector-anchored edge.
  Added `edge_kind` (one of `standard_standard`, `standard_domain`,
  `domain_standard`, `domain_domain`) computed on read for every equivalence
  response, an `?edge_kind=` filter on equivalence/translation endpoints,
  a `group_by=edge_kind` option on `/equivalences/stats`, and a new MCP tool
  `list_crosswalks_by_kind` (24 tools total). Provenance tags:
  `derived:sector_anchor:v1` and `derived:sector_anchor:v1:fanout`.

---

## Immediate - next 1-2 sessions

- [ ] **Email capture for taxonomy updates**
  A small "Get notified when new systems are added" form in the footer
  and/or after the hero stats section. Store email + consent in a
  `newsletter_subscriber` table. Low friction - no account required.
  Integrates with Resend/Mailchimp/SendGrid for delivery.

- [x] **GitHub stars badge**
  Live GitHub star count badge on hero stat pills and developers page.

---

## Short term - next few sessions

- [x] **Export / bulk download (gated behind free account)**
  CSV download buttons on every system page. Authenticated users get
  "All nodes" + per-crosswalk buttons. Unauthenticated users see a lock
  with a sign-in prompt. Backend: `/api/v1/systems/{id}/export.csv` and
  `/{id}/crosswalk/{target}/export.csv` (auth-gated StreamingResponse).

- [ ] **CI/CD pipeline (GitHub Actions)**
  A workflow that runs `pytest tests/ -q` on every push and pull request.
  Catches regressions before they reach production.
  Also add a lint step (ruff or flake8) and TypeScript check (`tsc --noEmit`).

- [ ] **Production deployment guide**
  Document the step-by-step process to deploy the backend (Fly.io or
  Railway) and frontend (Vercel). Include env vars, build commands,
  custom domain setup, and how to wire the Next.js proxy to the API.

- [x] **More country coverage on the world map**
  Added national classification systems for 6 large economies:
  - Brazil: CNAE 2.0 (21 sections, exact ISIC Rev 4 alignment)
  - China: CSIC 2017 (20 sections, ISIC Rev 4 aligned)
  - Russia: OKVED-2 (21 sections, NACE/ISIC exact alignment)
  - Indonesia: KBLI 2020 (21 sections, exact ISIC Rev 4 alignment)
  - Mexico: SCIAN 2018 (23 sectors, NAICS crosswalk)
  - South Africa: SIC-SA (21 sections, exact ISIC Rev 4 alignment)
  All wired into crosswalk_country_system.py as official links.

---

## Medium term

- [ ] **Use-case landing pages**
  Targeted pages for verticals that drive organic search traffic.
  Each page links to relevant systems, shows sample codes, and has
  a clear API/sign-up CTA.
  - `/healthcare` - LOINC, ICD-11, ATC WHO (searches like "ICD-11 API")
  - `/trade-customs` - HS 2022, CPC v2.1, UNSPSC (HS code lookup API)
  - `/compliance` - GDPR, CFR Title 49, ISO 31000 (GDPR article search)
  - `/hiring-workforce` - ISCO-08, SOC 2018, ESCO, O*NET (ISCO to SOC crosswalk)
  - `/patents` - Patent CPC (CPC code lookup API)

- [ ] **MCP / AI-focused outreach content**
  The MCP server is a differentiator - most data providers do not have one.
  Draft a short post for:
  - Anthropic Discord (#mcp-servers channel)
  - Hacker News (Show HN post)
  - MCP community forums / GitHub discussions
  Focus on the "ask Claude to translate a NAICS code to ISIC" angle.

---

## Longer term

- [ ] **Email notification system**
  When a new classification system is ingested or a major update is made,
  send a digest to newsletter subscribers. Triggered by an admin action
  or a new `changelog` table entry.

- [ ] **Enterprise contact / pricing page**
  A simple `/pricing` or `/enterprise` page with a contact form for
  teams that need higher rate limits, SLA guarantees, or custom
  crosswalk ingestion. Connects to email or a CRM.

- [ ] **Embeddable widget**
  A small JavaScript snippet that lets other sites embed a taxonomy
  search box or code lookup - drives awareness and inbound links.

- [ ] **API usage analytics dashboard (admin)**
  Show request counts, top endpoints, top users, and error rates from
  the `usage_log` table. Useful for understanding how the API is being
  used and spotting power users to convert to enterprise.

---

## Completed

- [x] REST API (FastAPI) - 13 endpoint groups, 82 systems
- [x] MCP server - 21 tools over stdio
- [x] Web app - Galaxy View, World Map, Industry Map, Browse by Category
- [x] Passwordless OAuth login - GitHub, Google, LinkedIn
- [x] Developers page - GitHub, API reference, MCP setup guide
- [x] For Developers section on home page (3 cards)
- [x] Expanded footer with Explore + Developers link columns
- [x] Header with Sign In / user dropdown
- [x] OAuth production setup guide (OAUTH_PRODUCTION_SETUP.md)
- [x] Full test suite - 2018+ tests, TDD throughout
- [x] GitHub stars badge (hero + developers page)
- [x] Export/bulk download - nodes CSV + crosswalk CSV, auth-gated (backend + frontend)
- [x] Country coverage - CNAE 2.0, CSIC 2017, OKVED-2, KBLI 2020, SCIAN 2018, SIC-SA
