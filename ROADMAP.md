# WorldOfTaxanomy - Roadmap

Work items organized by priority. Check off items as they are completed.

---

## Immediate - next 1-2 sessions

- [ ] **API key dashboard (frontend UI)**
  Backend is fully built. Users can sign in but cannot create or revoke
  API keys from the site. Without this the lead gen loop is broken.
  Pages needed: key list, create key, revoke key.

- [ ] **Production DB ingestion**
  Production Neon DB has only 12 of 88 systems loaded. Run `ingest all`
  (~30-40 min) to load all remaining systems, crosswalks, and domain
  taxonomies. World map, search, and MCP tools all become dramatically
  more useful. See `PLAN.md` for the exact command.

- [ ] **Email capture for taxonomy updates**
  A small "Get notified when new systems are added" form in the footer
  and/or after the hero stats section. Store email + consent in a
  `newsletter_subscriber` table. Low friction - no account required.
  Integrates with Resend/Mailchimp/SendGrid for delivery.

- [ ] **GitHub stars badge**
  Add a live GitHub star count badge to the hero stat pills and the
  developers page. Uses the GitHub public API (no auth needed).
  Social proof drives more stars, which drives organic discovery.

---

## Short term - next few sessions

- [ ] **Export / bulk download (gated behind free account)**
  Add CSV download buttons to system and crosswalk pages.
  Unauthenticated users see the button but are prompted to sign in.
  Downloads of interest: NAICS-ISIC crosswalk, full system node list,
  country coverage CSV. High-intent action - a strong lead signal.

- [ ] **CI/CD pipeline (GitHub Actions)**
  A workflow that runs `pytest tests/ -q` on every push and pull request.
  Catches regressions before they reach production.
  Also add a lint step (ruff or flake8) and TypeScript check (`tsc --noEmit`).

- [ ] **Production deployment guide**
  Document the step-by-step process to deploy the backend (Fly.io or
  Railway) and frontend (Vercel). Include env vars, build commands,
  custom domain setup, and how to wire the Next.js proxy to the API.

- [ ] **More country coverage on the world map**
  Add national classification systems for the largest uncovered
  economies so the world map shows more colour:
  - Brazil: CNAE 2.0
  - China: CSIC (Chinese Standard Industrial Classification)
  - Russia: OKVED 2
  - Indonesia: KBLI
  - Mexico: SCIAN
  - South Africa: SIC (SA)

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
- [x] Full test suite - 1944 tests, TDD throughout
