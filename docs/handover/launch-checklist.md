# Launch checklist

> **Master view of everything between today and WoT going public on
> `worldoftaxonomy.com`.** Pulls together the threads from
> `portfolio-auth.md`, `auth-implementation.md`, `cicd-deployment.md`,
> `description-backfill-summary` (PR #74), and the in-flight LLM
> coverage work. Updated 2026-04-29.

## Status snapshot

**All seven soft-launch sections are code-complete.** What remains
is operator action (deploy + configure + smoke), not engineering.

- **Section 1 (Cloud Run migration)**: done pre-Phase-6.
- **Section 2 (LLM coverage)**: 63%+ on the 1,000 systems; further
  rounds can run post-launch in the background.
- **Section 3 (developer-key system)**: shipped via PRs #119, #121,
  #122, #124, #125, #126 (all merged).
- **Section 4 (marketing site)**: shipped via PRs #129, #130, #131
  (all merged).
- **Section 5 (MCP installation flow)**: PRs #135, #136, #137 open
  as drafts and pending review. First PyPI release happens on the
  next `vX.Y.Z` tag push after the trusted-publisher setup on PyPI
  is done.
- **Section 6 (operational baseline)**: shipped via PR #133
  (merged).
- **Section 7 (legal + brand basics)**: shipped via PR #132
  (merged).

The remaining operator items (Cloud SQL migration apply, Resend
secret provisioning, Cloud Run alert provisioning, manual smoke
walkthrough on prod, first PyPI release) are itemized inline in
each section below.

## Launch tiers

Three milestones, not one. Don't conflate them:

1. **Soft launch (private beta)**: friends-and-family, <50 users, no
   public marketing. Goal: shake out integration bugs, validate the
   email gate UX, get real API/MCP usage data.
2. **Public launch**: HN/X/LinkedIn announcement, public sign-ups
   open, marketing site live. Goal: the demand validation moment.
3. **Pro-tier launch**: Stripe wired, paid plans available. Goal:
   first paying customer.

Soft launch is the near-term target. Public and Pro launches are
later milestones with their own checklists; soft-launch is what this
doc focuses on.

## Soft-launch critical path

Items below are in the order they should land. Each links to its
home doc where one exists.

### 1. Cloud Run migration completes

Owner: in flight, see PR #1.

- [ ] Cloud Run service deployed at `wot.aixcelerator.ai`.
- [ ] DNS cut over from `wot.aixcelerator.app` (legacy).
- [ ] CORS allow-list updated for `worldoftaxonomy.com`.
- [ ] OAuth callback URLs updated for any current providers (email
      gate is the only flow today, so this is mostly a no-op).
- [ ] Health check endpoint (`/health`) returning 200 from prod.

**Why first**: every later step references the new domain. Don't
build on top of a domain that's about to move.

### 2. LLM coverage round-trip

Owner: ongoing, see [description-backfill-summary](./description-backfill-summary.md)
(PR #74).

- [x] Round 3 (Track 1 LLM, ~2,900 rows) complete.
- [ ] Round 4 (Track 1 LLM, ~3,400 rows) in flight at time of writing.
- [ ] Cascade run after Round 4 lands canonical parents (NACE/ISIC):
      `python -m scripts.mirror_descriptions --from nace_rev2`,
      `python -m scripts.mirror_descriptions --from isic_rev4`.
      Expected ~23K rows.
- [ ] Refresh `coverage-report.md` once cascade completes.

After all the above: coverage should land near 65-66%. Higher
percentages (Patent CPC, ICD-10-CM, UNSPSC, ICD-11) are Track 2 LLM
work and not soft-launch blockers - they can run post-launch in the
background.

**Why second**: credibility. The product's value prop is
"comprehensive global classification graph." Below 60% coverage on
high-traffic systems undermines that claim. 63% with the headline
systems (NAICS, ISIC, NACE, NIC, etc.) at 95%+ is launch-ready.

### 3. Phase 6 - developer-key issuance system

Owner: see [auth-implementation.md](./auth-implementation.md) Phase 6.

**Status: implementation complete, four PRs open as drafts**
(2026-04-28). Merge order is #119 -> #121 -> #122 -> #124. Soft
launch is unblocked once the chain merges and the migration runs on
Cloud SQL.

- [x] `app_user` schema migration: `email UNIQUE NOT NULL`,
      `org_id NOT NULL`, `zitadel_sub` (NULL until Phase 2),
      `role`, `revoked_at`, `last_used_at`. (PR #119)
- [x] `org` table: `kind`, `domain UNIQUE`, `tier`,
      `rate_limit_pool_per_minute`, `stripe_customer_id`,
      `zitadel_org_id`. (PR #119)
- [x] `api_key` table: `scopes TEXT[]`, expiry, audit columns. (PR #119)
- [x] Backfill existing users into per-domain corporate orgs (or
      per-email personal orgs for free-email domains). Legacy keys
      backfilled with `scopes=['wot:*']`. (PR #119,
      `migrations/003_phase6_developer_keys.sql`)
- [x] Magic-link auth flow on `/developers`. (PR #121)
- [x] `/api/v1/developers/keys` CRUD endpoints with scope check.
      (PR #121)
- [x] Helpful 401 / 403 responses pointing at `/developers` and
      `/pricing`, with `WWW-Authenticate: ApiKey` and `Link: <...>;
      rel="signup"|"manage"|"upgrade"` headers. (PR #121, #124)
- [x] Resend integration with `NoopEmailClient` fallback when
      `RESEND_API_KEY` is unset. (PR #121,
      `world_of_taxonomy/auth/email.py`)
- [x] `/developers/signup` landing + `/developers/keys` dashboard +
      `/auth/magic` callback. (PR #121)
- [x] Tests covering: prefix derivation, scope validation,
      magic-link round-trip, rate-limit org bucketing, revocation,
      tier enforcement on bulk export and classify. 88 new tests
      across the four PRs.
- [x] MCP server fails loud at startup when `WOT_API_KEY` and
      `DATABASE_URL` are both unset; actionable stderr message
      pointing at `/developers`. (PR #122)
- [x] Existing gated endpoints (bulk export, classify,
      nodes/generate) wired onto `Depends(require_scope)` /
      `Depends(require_tier)`. (PR #124)
- [ ] **Manual smoke after merge:** signup -> key in inbox -> key
      works on `/api/v1/systems/naics_2022` -> revoke -> key returns
      401 within ~2 seconds.
- [ ] **Cloud SQL migration:** deploy engineer runs
      `migrations/003_phase6_developer_keys.sql` against prod with
      `psql --single-transaction -v ON_ERROR_STOP=1`. Local
      `wot-postgres` migration verified clean (2026-04-28).
- [ ] **Resend account:** set `RESEND_API_KEY` in GCP Secret Manager
      before public traffic; signup endpoint silently drops mail
      until then (NoopEmailClient logs a warning).

Estimated 1.5 days; actual ~1 day across four PRs. **This is the
launch gate**: without it, every public API/MCP request is
anonymous-rate-limited (30 req/min), which is hostile to early
adopters.

### 4. Marketing site (worldoftaxonomy.com)

**Status: code-complete** (2026-04-29). Shipped via merged PRs
#129 (developers landing CTA) and #130 (Section 4 marketing).

- [x] Hero copy + value prop confirmed.
- [x] `/explore` (search) - already built.
- [x] `/system/[id]/...` - already built.
- [x] `/dashboard` - already built.
- [x] `/developers` - shipped with Phase 6 + the new
      "Get a free API key" / "Manage your keys" CTAs (PR #129).
- [x] `/pricing` - "Free / Pro / Enterprise" tiers with the
      "Public beta - all plans free" amber banner (PR #130).
      Free-tier CTA points at `/sign-in?next=/developers/keys`
      (after PR #131 universal sign-in landed).
- [x] `/guide` (wiki pages) - already built; sanity-check still
      a periodic-review item, not a launch blocker.
- [x] `/guide/api-keys` - new, points users at `/developers`.
      (PR #130)
- [x] `/guide/mcp-setup` - rewritten to match the published PyPI
      package (`uvx worldoftaxonomy-mcp`, no npm path). See PR #137
      below.
- [x] Footer: Legal column with terms / privacy / source attribution
      (PR #132); Developers column with API-key + pricing + contact
      links (PR #130); contact form delivers via /api/v1/contact, no
      public mailto.
- [ ] OpenGraph + favicon + analytics (PostHog or Plausible -
      decision deferred). Not a launch blocker; can ship same-day
      as the public-launch announcement.
- [x] `llms-full.txt` regenerated and published at
      `/llms-full.txt`.

### 5. MCP installation flow validated

**Status: code-complete** (2026-04-29). Three PRs cover the flow.
First PyPI release happens on the next `vX.Y.Z` tag push after the
trusted-publisher setup on PyPI is done; that flips the final
checkbox below.

- [x] **MCP HTTP-mode dispatch.** Decision: PyPI distribution
      (`worldoftaxonomy-mcp`), no npm. The dispatcher maps each MCP
      tool to a REST call against `wot.aixcelerator.ai` with a
      `WOT_API_KEY` Bearer header. 22 of 26 tools wired today; the
      remaining 3 (`list_crosswalks_by_kind`, `get_country_scope`,
      `get_audit_report`) raise a clean "not yet supported in HTTP
      mode" error and are documented as DB-only. (PR #135)
- [x] **PyPI packaging.** Single `pyproject.toml` at the repo root
      ships dist `worldoftaxonomy-mcp` with a small default deps set
      (httpx + asyncpg + python-dotenv, ~5 MB wheel) plus an
      optional `[server]` extra for self-hosters. Two console
      scripts: `worldoftaxonomy-mcp` (the new MCP entry) and
      `world-of-taxonomy` (the existing multi-subcommand CLI).
      `setup.py` removed. (PR #136)
- [x] **GitHub Actions tag-based publish.**
      `.github/workflows/publish-pypi.yml` triggers on `vX.Y.Z` /
      `vX.Y.Zrc1` tags, validates the tag matches `pyproject.toml`,
      builds wheel + sdist, smoke-tests the wheel installs cleanly
      and the entry-point fails closed without env vars, then
      publishes via PyPI **trusted publishing (OIDC)** - no token
      stored anywhere. (PR #136)
- [x] **`/guide/mcp-setup` rewrite.** Walks users through getting a
      key, configuring Claude Desktop / Cursor / Zed / VS Code
      Continue / Windsurf, verifying the wiring with a one-shot
      stdin probe, and the error responses they may hit. All
      examples use `uvx worldoftaxonomy-mcp`; no npm references
      anywhere. (PR #137)
- [x] **MCP server fails loud at startup** if neither `WOT_API_KEY`
      nor `DATABASE_URL` is set. (PR #122, already merged.)
- [ ] **First PyPI release.** Pre-requisites:
      1. Create the project on
         https://pypi.org/manage/projects/worldoftaxonomy-mcp/.
      2. Add this workflow as a trusted publisher
         (`colaberry`/`WorldOfTaxonomy`/`publish-pypi.yml`/`pypi`).
         See [`docs/handover/pypi-release.md`](./pypi-release.md).
      3. `git tag v0.1.0 && git push origin v0.1.0`. Workflow
         publishes ~5 minutes later via OIDC.
- [ ] **At least one Claude Desktop user end-to-end without help**
      (Ram). Run `uvx worldoftaxonomy-mcp` from a fresh Mac, drop
      the config snippet into `claude_desktop_config.json`,
      restart, ask "convert NAICS 5417 to NACE", confirm the model
      calls `get_equivalences` or `translate_code`. Records the
      first end-user smoke time.

### 6. Operational baseline

- [x] Sentry (or equivalent) wired for backend exceptions. Starlette
      + FastAPI integrations active when `SENTRY_DSN` is set;
      before_send scrubs Authorization headers, cookies, and the
      `dev_session` cookie value. Tier / org_id / user_id annotated
      on every request via the rate-limit middleware. (PR #133)
- [x] Cloud Run alerts: 5xx rate > 1%, latency p95 > 2s, instance
      restart loop. Provisioning script:
      `scripts/phase6_setup_alerts.sh` (idempotent; re-running upserts
      thresholds). (PR #133)
- [ ] Daily backup of Postgres confirmed enabled. Cloud SQL has
      automatic backups on by default; verify in the deploy step.
      Verification one-liner:
      `gcloud sql instances describe wot-prod
       --format='value(settings.backupConfiguration)'`
- [x] On-call rotation. Just Ram for now; documented in
      [`runbooks/README.md`](./runbooks/README.md) "On-call rotation"
      section. Add a co-on-call before the first paying customer.
      (PR #133)
- [x] Runbooks: "API is 5xx-ing", "key validation is slow", "Cloud
      Run cold start spike". All three under
      [`docs/handover/runbooks/`](./runbooks/) with a fixed structure
      (Triage / Common causes / Mitigation / Root cause / Followups).
      (PR #133)
- [x] **Bot / abuse defense layers A + B + C-doc.** (PR #140)
  - **A (in-process per-IP rate guard):** 5/hour on
    `/api/v1/developers/signup`, 30/min on `/api/v1/auth/magic-callback`.
    Honors `X-Forwarded-For`. 429 with `Retry-After` + structured detail.
  - **B (DB-backed email-send budget):** `email_send_log` table
    (migration 004) caps Resend sends at 200/hour globally
    (env-tunable via `EMAIL_SEND_BUDGET_PER_HOUR`). 503 with
    `Retry-After` when cap trips - protects spend even if a botnet
    bypasses the per-IP cap.
  - **C (Cloudflare runbook):** ops task documented at
    [`runbooks/cloudflare-edge.md`](./runbooks/cloudflare-edge.md).
    Free-tier Bot Fight Mode + WAF + edge rate-limit on signup.
    To be wired in Cloudflare dashboard; runbook is the playbook.
- [ ] **Cloudflare in front of Cloud Run** (Layer C) per the runbook.
      ~1 hour of Cloudflare dashboard work. Drops scrapers + basic L7
      DDoS before they reach origin.
- [ ] Sentry-test smoke: set `SENTRY_TEST_TOKEN` on Cloud Run, then
      `curl -X POST -H "X-Sentry-Test-Token: $TOKEN" .../api/v1/_internal/sentry-test`
      and confirm the event lands in the Sentry inbox. Then unset
      the token (it stays out of prod config except for testing).

### 7. Legal + brand basics

**Status: code-complete** (2026-04-29). All three pages and the
footer Legal column shipped via PR #132.

- [x] **Terms of Service** at `/legal/terms`. Calibrated for
      "open beta, no paid plans yet": acceptable use, API-key
      responsibility, source-data attribution boilerplate, MIT
      software-license note, no-warranty + liability cap. Last
      updated date in the page itself; bump when material changes
      ship. (PR #132)
- [x] **Privacy policy** at `/legal/privacy`. Plain-English
      summary plus a table of every data class collected (email,
      hashed keys, IP, request metadata, `dev_session` cookie,
      classify lead emails) with retention. Names sub-processors
      (GCP Cloud Run / Cloud SQL / Secret Manager, Resend, Sentry,
      GitHub). User-rights section (access / correction /
      deletion / portability / objection) routes through the
      contact form for identity verification. (PR #132)
- [x] **Attribution page** at `/legal/attribution`. Catalog of
      source publishers grouped by domain (industry, geo, trade,
      occupational, education, health, financial+regulatory,
      domain taxonomies). Each entry names the authority and
      license. Calls out redistribution constraints (LOINC
      license, ATC commercial-use license, trademarked
      CPT/SNOMED/DSM-5/ISO standards we carry only as nav
      skeletons). (PR #132)
- [ ] Cookie banner (only if EU traffic expected). The `dev_session`
      cookie is essentials-only (no consent required under most
      interpretations); defer until the first EU prospect asks. Not
      a launch blocker.

## Public-launch checklist (after soft launch settles)

The following don't gate soft launch but should land before a public
HN/X/LinkedIn push:

- [ ] Pricing page with real numbers (free / pro / enterprise).
- [ ] Stripe integration (Phase 6 + new billing module).
- [ ] Phase 1-5 of `auth-implementation.md` (Zitadel + Permit.io)
      done in staging, ready to flip in prod.
- [ ] At least 5 customer testimonials or case studies on the
      landing page.
- [ ] SEO baseline: meta tags, sitemap, robots.txt validated.
- [ ] Press kit (logo files, screenshots, one-paragraph description).
- [ ] Demo video (~2 min) on the landing page.
- [ ] Status page (statuspage.io / Better Stack / hosted equivalent).

## Pro-launch checklist (first paying customer)

Even later. Tracked here for visibility but no immediate work:

- [ ] Stripe customer portal integrated for self-service billing.
- [ ] Pro tier limit enforcement (10K req/min pool).
- [ ] Enterprise tier flow (sales-led, custom contracts).
- [ ] Phase 4 (Permit.io) live in prod.
- [ ] Phase 7 (extract `developer.aixcelerator.ai`) if WoO is
      starting in parallel.

## Open dependencies on third parties

| Dependency | Status | Trigger to revisit |
|---|---|---|
| Zitadel Cloud account provisioned | Not yet (free tier sufficient initially) | When magic-link is no longer enough or WoO ships |
| Permit.io account provisioned | Not yet | When Phase 4 starts |
| Resend / Postmark / SES account | Not yet | Phase 6 prerequisite |
| Stripe account | Not yet | Pro launch |
| Domain registrar for `aixcelerator.ai` | Owned per memory | DNS records for sibling product launches |
| GCP project for Cloud Run + Cloud SQL | Active per memory | None |
| GitHub Secret Scanning Partner enrollment | Not yet | Post-launch (when leak detection becomes valuable) |

## Risk register

Top risks ordered by likelihood × impact:

1. **Round 4 LLM run dies overnight or hits API quota.** Mitigation:
   the script is cache-resumable; restart picks up where it left off.
   Round 4 is small enough (~3,400 rows) to absorb a 1-2 hour
   interruption. **Likelihood: low. Impact: low.**

2. **Cloud Run migration introduces a regression.** Mitigation: keep
   `wot.aixcelerator.app` running for 48 hours post-cutover with DNS
   pointing to the new service; if anything breaks, flip DNS back.
   **Likelihood: medium. Impact: medium.**

3. **Phase 6 implementation discovers Resend deliverability issues
   for magic links.** Mitigation: have a fallback (Postmark) ready
   to swap if delivery rates dip below 95%. Test with personal Gmail,
   Outlook, ProtonMail, Yahoo, FastMail accounts before public launch.
   **Likelihood: medium. Impact: high (broken sign-up funnel).**

4. **First public-launch traffic spike overwhelms the free-tier
   Cloud Run instance.** Mitigation: configure auto-scaling
   (min=1, max=10) before public launch. Cloud SQL scales
   independently. **Likelihood: low for soft launch, medium for
   public launch. Impact: medium.**

5. **A major LLM-generated description turns out to be wrong (e.g.,
   wrong year for a regulation, inverted causation in a clinical
   note) and gets flagged on social media.** Mitigation: ship with a
   visible "Report incorrect description" link on every node detail
   page; have a triage process. The Track 2 verified-LLM pipeline
   reduces this risk to ~2% per row, but at 760k rows that's still
   ~15k potentially-wrong rows. **Likelihood: medium. Impact: high
   for credibility.**

## What this checklist deliberately leaves out

- Internal team scaling, hiring, contractor onboarding.
- Specific marketing tactics (HN timing, LinkedIn schedule, etc.) -
  belongs in a separate marketing doc.
- Specific pricing numbers - decision deferred to Pro launch.
- WoO / WoUC / WoA scope - tracked in `portfolio-auth.md` and the
  per-product TBD docs.
- Multi-region deployment - single us-central1 is fine for soft
  launch.
- Multi-language support - English only.

## Recommended sequencing summary

```
[ in flight ] Round 4 LLM + cascade            -> coverage to ~65%
[ in flight ] Cloud Run migration (PR #1)      -> wot.aixcelerator.ai live
[ ~1.5 days ] Phase 6 developer-key system     -> the launch gate
[ ~1 day   ] Marketing site polish + /developers -> soft-launch ready
[ ~half day ] MCP install guide + smoke test   -> end-to-end demo works
[ ~1 day   ] Ops baseline (Sentry, alerts, runbooks) -> safe to go live

------------ SOFT LAUNCH (private beta) ------------

[ days-weeks ] Customer feedback, validate demand, iterate
[ ~1 week  ] Phase 1-5 (Zitadel + Permit.io) when ready

------------ PUBLIC LAUNCH ------------

[ ~3 days  ] Stripe + pricing page
[ ~2 days  ] Phase 7 if WoO is in flight

------------ PRO LAUNCH ------------
```

Total wall-clock from today to soft launch: ~5-7 days of focused
work, gated on Cloud Run PR #1 landing and Round 4 LLM finishing.
Public launch is another 1-2 weeks beyond that. Pro launch when the
first prospect actually wants to pay.
