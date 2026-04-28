# Launch Handover for the Deployment Developer

> **Hi - if you're reading this, you've been asked to take WorldOfTaxonomy
> from "code is ready" to "users are using it." This doc is your onboarding
> in one read. It points you at the specific docs you need, lists the work
> in implementation order, and flags the decisions that need Ram's input
> before you proceed.**
>
> Owner of this doc: Ram Katamaraja (`ram@colaberry.com`).
> Last refresh: 2026-04-27.

## What you are deploying

A unified global classification knowledge graph: 1,000 systems,
1.2M nodes, 321K crosswalk edges, exposed as a REST API, an MCP
server (for AI agents), and a Next.js web app.

Three artifacts:

| Service | What it serves | Domain |
|---|---|---|
| `wot-web` | Next.js 16 frontend (App Router) | `worldoftaxonomy.com` |
| `wot-api` | FastAPI REST + MCP stdio server | `wot.aixcelerator.ai` |
| `wot-db` | Cloud SQL Postgres 15 | (private, accessed via socket) |

Tech stack, schema, and architecture are documented at:
- [docs/handover/backend.md](backend.md)
- [docs/handover/frontend.md](frontend.md)
- [HANDOVER.md](../../HANDOVER.md) for the 30-minute project tour

## Your mission - soft launch

Three launch tiers. We are aiming at #1 only:

1. **Soft launch (private beta)**: <50 users, friends and family, no
   public marketing. Goal: shake out integration bugs, validate the
   email gate UX, get real API/MCP usage data. **This is what you
   are deploying.**
2. **Public launch**: HN/X/LinkedIn announcement (later, not yours).
3. **Pro-tier launch**: Stripe wired (later, not yours).

The detailed master view is in [launch-checklist.md](launch-checklist.md);
it's the source of truth for what is and isn't in scope. This doc
boils that down to your specific work.

## What's already done (you can skip)

| | Status | Where |
|---|---|---|
| Code complete: API + MCP + frontend | ✅ on `main` | this repo |
| Description coverage at 65.71% | ✅ | [coverage-report.md](coverage-report.md) |
| Auth design locked (Zitadel + Permit.io + magic-link keys) | ✅ design only | [portfolio-auth.md](portfolio-auth.md), [auth-implementation.md](auth-implementation.md) |
| MCP install guide for end users | ✅ landed | [wiki/mcp-setup.md](../../wiki/mcp-setup.md) |
| Per-system description backfills | ✅ all merged | (45 PRs landed today) |
| Track 2 verified-LLM pipeline scaffold | ✅ paused, resumable | `scripts/track2_watchdog.sh` |

## Database state and seeding production (read this BEFORE you start)

**Important reality**: the descriptions data you'll see in the
codebase (1.2M nodes, 65.71% description coverage as of 2026-04-27)
**lives only on Ram's laptop**, not in this repo. Specifically:

| Data | Where it lives | In repo? |
|---|---|---|
| Schema (`schema.sql`, `schema_auth.sql`, migrations) | git | ✅ |
| Per-system ingester scripts | git | ✅ |
| Source data files (`data/*.csv`, `*.xml`, `*.zip`) | gitignored (`data/*` in `.gitignore`) | ❌ |
| LLM caches (`data/llm_descriptions/*.jsonl`, `data/llm_verified/*.jsonl`) | gitignored | ❌ |
| **Populated Postgres database** with descriptions for 793,230 nodes | **Ram's local Postgres only** | ❌ |

If you deploy Cloud Run + Cloud SQL with a fresh schema, you get an
**empty database**. The frontend will work but every system will
show 0 nodes, and the API will return empty arrays. Not viable for
any flavor of launch.

**The plan**: Ram dumps his local Postgres and uploads to a
Google Drive folder he shares with you. You download it, push it
through a one-shot GCS bucket (Cloud SQL's `import sql` only reads
from `gs://`), and restore into Cloud SQL on first deploy.
~1-3 GB compressed dump.

### Step 0 (before Step 1) - receive the database dump from Ram

Ram will upload a recent `pg_dump` of his local DB to a Google
Drive folder and share the link with you. This is the operator-
friendly path; the actual restore into Cloud SQL still happens
through GCS (one short bridge step on your side, see below).

The handoff:

```bash
# Ram runs this on his laptop (~30 min depending on disk + compression)
pg_dump -d worldoftaxanomy -F c -Z 9 -f wot_db_$(date +%Y-%m-%d).dump

# Ram uploads the .dump to a Google Drive folder and shares the
# folder with your email at "Editor" (or "Viewer" if download-only
# is acceptable).
```

You receive a Google Drive folder URL with the dump file inside.
Expected dump size: 1-3 GB compressed.

### Restoring the dump into Cloud SQL

After Cloud SQL is provisioned (Step 2 below) and before Phase 6
key issuance (Step 4):

```bash
# 1. Download the dump from Drive to your laptop. Either:
#      a) browser download from the shared folder, or
#      b) `gdown` / `rclone` CLI for non-browser environments.
#    Save to ~/Downloads/wot_db_<date>.dump

# 2. Create a one-shot GCS bucket for the bootstrap upload.
#    Cloud SQL's `import sql` reads only from gs:// URLs, so this
#    bridge step is unavoidable.
gsutil mb -l us-central1 gs://wot-deploy-bootstrap/

# 3. Upload the local file to GCS.
gsutil cp ~/Downloads/wot_db_<date>.dump gs://wot-deploy-bootstrap/

# 4. Grant Cloud SQL service account read access on the bucket.
SA=$(gcloud sql instances describe wot-db \
       --format='value(serviceAccountEmailAddress)')
gsutil iam ch serviceAccount:${SA}:objectViewer gs://wot-deploy-bootstrap/

# 5. Import. Cloud SQL handles the streaming restore.
gcloud sql import sql wot-db \
  gs://wot-deploy-bootstrap/wot_db_<date>.dump \
  --database=worldoftaxanomy

# 6. Verify
gcloud sql connect wot-db --user=postgres --database=worldoftaxanomy \
  --quiet -e "SELECT COUNT(*) FROM classification_node;"
# expected: ~1,212,486

# 7. Tear down the bootstrap bucket once verified
gsutil rm -r gs://wot-deploy-bootstrap/
```

The Drive folder stays as the canonical archive; the GCS bucket
is throwaway. The restore is a one-time operation. After this,
ongoing data updates flow through ingester re-runs (scheduled or
triggered), not dump+restore.

### What if you can't get the Drive link?

Fall back to **re-running every ingester in production**. Read
[docs/handover/description-backfill.md](description-backfill.md)
for the full sequence. Estimate ~3 days + ~$200-500 in LLM API
spend (the `backfill_llm_*.py` scripts call Ollama Cloud).

This is the worst path - last resort only. Ask Ram before going
this way.

## What you must do (in order)

### 1. Get access (day 1, before any deploy work)

Ask Ram for:

- [ ] GitHub write access to `colaberry/WorldOfTaxonomy`
- [ ] GCP project Owner or Editor role on the production project
- [ ] DNS access for `aixcelerator.ai` and `worldoftaxonomy.com`
- [ ] Vercel team membership (if frontend is deploying via Vercel - confirm with Ram, see decision #3 below)
- [ ] Resend / Postmark / SES sender account (if you're wiring email - confirm scope with Ram)
- [ ] Read access to the `1Password / vault` where Zitadel + Permit.io credentials will live (those are not yet provisioned; out of soft-launch scope)
- [ ] **Google Drive folder access for the database dump** (see "Step 0" above; Ram shares the folder with your email)

Verify with:

```bash
gh auth status
gcloud config get project
nslookup wot.aixcelerator.ai
```

If any of these fail, stop and message Ram. **Do not provision anything in the wrong project.**

### 2. Cloud Run migration to wot.aixcelerator.ai (the launch-blocker)

This is in flight as **PR #1** at the time of writing. Status check
with Ram: is it merged? In review? Stuck?

If not yet merged:
- Read [docs/handover/cicd-deployment.md](cicd-deployment.md) end to end.
- Read [docs/runbooks/gcp-deploy.md](../runbooks/gcp-deploy.md) for the
  command-by-command setup.
- Verify the staging Cloud Run service is healthy at the staging URL
  before touching prod.

If already merged: confirm prod health. Run:

```bash
curl -fsS https://wot.aixcelerator.ai/api/v1/healthz
curl -fsS https://wot.aixcelerator.ai/api/v1/systems | head -c 500
```

The first call should return `{"status":"ok"}` or similar. The
second should return a JSON list of classification systems.

Verification gate before proceeding to step 3:
- [ ] Cloud Run revision deployed at `wot.aixcelerator.ai`
- [ ] DNS cut over from `wot.aixcelerator.app` (legacy)
- [ ] `/api/v1/healthz` returning 200 from the public URL
- [ ] CORS allow-list updated for `worldoftaxonomy.com` (request from a browser at that origin succeeds)
- [ ] Cloud Logging is capturing structured logs (`gcloud run services logs read wot-api --limit 5`)

### 3. Operational baseline (do this *before* shipping anything else)

Without this, soft launch users will hit silent breakage and you
won't know.

- [ ] **Sentry** (or equivalent) wired into both `wot-api` and
  `wot-web`. Backend uses `SENTRY_DSN` env var; see
  [docs/handover/backend.md §Observability](backend.md#observability).
- [ ] **Cloud Run alerts** configured for: 5xx rate >1%, p95 latency
  >2s, instance restart loop, container OOM.
- [ ] **Cloud SQL automatic backups** enabled (verify in console).
- [ ] **Status page** deferred to public-launch milestone unless
  Ram says otherwise.
- [ ] **On-call rotation**: just Ram for soft launch.

Document the alert thresholds you choose in
[docs/runbooks/](../runbooks/) and link from
[cicd-deployment.md](cicd-deployment.md).

### 4. Ship the developer-key system (Phase 6 of auth-implementation)

This is the launch gate for API + MCP. Without it, every public
API request is anonymous-rate-limited at 30 req/min, which is
hostile to early adopters.

Read [auth-implementation.md - Phase 6](auth-implementation.md#phase-6---developer-key-issuance-and-lifecycle-1-pr-15-days)
in full before writing code. Key constraints from that doc that
must survive into your implementation:

- `app_user.email` is `UNIQUE NOT NULL`.
- `app_user.org_id` is `NOT NULL` from day 1 (every user belongs to
  exactly one org; throttling is always at the org level).
- Free-tier corp orgs share a 1,000 req/min pool across employees;
  free-email-domain users get per-user "personal" orgs.
- Key prefix encodes scope: `wot_` for WoT-only full access,
  `rwot_` for restricted, `aix_` for cross-product.
- Magic-link auth (no password). Reuse existing `app_user` /
  `api_key` tables; add the columns specified in Phase 6.

Estimated 1.5 days. Verification gate:
- [ ] `pytest tests/test_keys.py -v` passes.
- [ ] Manual smoke: signup at `/developers` -> key arrives in inbox
  -> `curl -H "Authorization: Bearer wot_..." /api/v1/systems/naics_2022`
  returns 200 -> revoke from dashboard -> next call returns 401
  within 2 sec.
- [ ] Anonymous calls hitting protected endpoints return JSON with
  a `signup` `Link:` header (per Phase 6).

### 5. Marketing site polish (~1 day)

The frontend is mostly done. What you need to verify or add:

- [ ] `/developers` lands cleanly (created by Phase 6 work).
- [ ] `/pricing` placeholder page: "Free during beta; paid plans
  coming." Per Ram's call, do not put numbers on it for soft
  launch.
- [ ] `/guide/api-keys` and `/guide/mcp-setup` exist and link to
  `/developers`. The MCP guide already exists at
  [wiki/mcp-setup.md](../../wiki/mcp-setup.md); confirm it renders
  through the wiki loader at `/guide/mcp-setup`.
- [ ] Footer: terms, privacy, contact form (no public email - per
  memory `feedback_no_public_email`).
- [ ] OpenGraph tags + favicon + analytics. **Ask Ram which
  analytics provider** (PostHog vs Plausible decision deferred).

### 6. Legal and brand basics

- [ ] Terms of Service: lift from a template (e.g. Vercel's open
  ToS), customize for "early beta, no paid plans yet."
- [ ] Privacy policy: covers email collection from `/classify`,
  magic-link cookies, IP logging in audit trail.
- [ ] Attribution page for upstream taxonomies (Census, UN, WHO,
  etc.). Most of these require attribution per their licenses.
  See [DATA_SOURCES.md](../../DATA_SOURCES.md).
- [ ] Cookie banner: skip if US-only soft launch; required if EU
  traffic expected. **Ask Ram.**

### 7. Smoke test the soft-launch funnel end to end

Before declaring soft launch open:

- [ ] Sign up at `worldoftaxonomy.com/developers` with a fresh
  email. Receive key in inbox within 30 sec.
- [ ] Use the key in `curl` against `/api/v1/systems/naics_2022`.
  Returns 200.
- [ ] Use the key in Claude Desktop's `mcp.json` per
  [wiki/mcp-setup.md](../../wiki/mcp-setup.md). Ask the assistant
  "what's NAICS 5417?" and verify the MCP tool fires.
- [ ] Visit `/explore`, `/system/naics_2022`, `/system/naics_2022/node/5417`.
  Page loads under 2s, no console errors.
- [ ] Revoke the key on `/developers/keys`. Next API call returns 401.
- [ ] Test on Safari, Chrome, Firefox, mobile Safari.

If all green, you're ready for soft launch.

## Decisions Ram needs to make (do not decide these yourself)

| # | Decision | Why it matters | Default if not heard |
|---|---|---|---|
| 0 | **Where to put the database dump and who to share it with** | Step 0 / soft-launch blocker. The dump is the only practical path to a populated Cloud SQL without re-running ~3 days of ingest. | Google Drive folder, share with the deployment dev's email |
| 1 | Email service: Resend vs Postmark vs SES | Phase 6 prerequisite. Affects deliverability and cost. | Resend |
| 2 | Analytics: PostHog vs Plausible vs none | Per-page tracking on the marketing site | none for soft launch |
| 3 | Frontend hosting: Vercel vs Cloud Run | Already decided per memory: `worldoftaxonomy.com` on Vercel. Confirm before deploying. | per memory: Vercel |
| 4 | Cookie banner needed for soft launch | Depends on whether EU traffic is expected | skip for US-only soft launch |
| 5 | When to start Phase 1-5 (Zitadel migration) | Soft-launch unblocked without it; public-launch needs it | after soft launch |

## Decisions you can make yourself

- Specific Sentry alert thresholds (above the project floor of 1%
  5xx, 2s p95)
- Specific Cloud SQL instance size and backup retention
- Cloud Build vs GitHub Actions for the deploy step (cicd-deployment
  is currently Cloud Build)
- Specific tokens / claims structure on the API key (within the
  scope/prefix model from Phase 6)
- Logging format and verbosity
- Test environment naming

## Communications

- **Daily check-in with Ram**: 10 min, async or call. What you
  shipped, what you're stuck on.
- **Sign-off gate**: anything that requires a "Decisions Ram needs
  to make" answer pauses until Ram replies. Do not guess.
- **Escalation**: production incident -> message Ram directly. No
  third party is on call for soft launch.
- **PR review**: tag `@ramdhanyk` on every non-trivial PR. Do not
  self-merge production-affecting changes without review.

## Where to look for what

| You need... | Read this |
|---|---|
| The full launch master view | [launch-checklist.md](launch-checklist.md) |
| Step-by-step Phases 0-9 of auth | [auth-implementation.md](auth-implementation.md) |
| The auth design rationale | [portfolio-auth.md](portfolio-auth.md) |
| CI/CD pipeline details | [cicd-deployment.md](cicd-deployment.md) |
| GCP setup commands | [docs/runbooks/gcp-deploy.md](../runbooks/gcp-deploy.md) |
| Rollback playbook | [docs/runbooks/deploy-rollback.md](../runbooks/deploy-rollback.md) |
| DB outage playbook | [docs/runbooks/db-down.md](../runbooks/db-down.md) |
| Migration playbook | [docs/runbooks/migrations.md](../runbooks/migrations.md) |
| Backend internals | [backend.md](backend.md) |
| Frontend internals | [frontend.md](frontend.md) |
| Per-system coverage report | [coverage-report.md](coverage-report.md) |
| Description-backfill series narrative | [description-backfill.md](description-backfill.md) |
| Domain crosswalk integration | [domain-crosswalk-integration.md](domain-crosswalk-integration.md) |
| Project tour / 30-min onboarding | [HANDOVER.md](../../HANDOVER.md) |
| 1,000-system catalog | [CLAUDE.md](../../CLAUDE.md) |

## What's NOT your problem (for clarity)

- Description coverage. The CPC Track 2 backfill is paused and
  durable; it's not on the soft-launch critical path.
- Zitadel / Permit.io provisioning (Phases 1-5 of
  auth-implementation). Soft launch ships with magic-link only;
  Zitadel comes later.
- Stripe billing (Phase 9). Pro launch only.
- Public marketing (HN, X, LinkedIn posts). Not your job. Public
  launch = post-soft-launch.
- Multi-region deployment. Single us-central1 is fine for soft
  launch.
- Mobile apps. Web only.
- WoO / WoUC / WoA sibling products. Each ships separately later.

## Definition of "soft launch is ready"

All of these green:

- [ ] `wot.aixcelerator.ai/api/v1/healthz` returns 200 from public
  internet
- [ ] **Cloud SQL has the dump restored: `SELECT COUNT(*) FROM classification_node` returns ~1,212,486**
- [ ] **Spot-check: `SELECT COUNT(*) FROM classification_node WHERE description IS NOT NULL AND description <> ''` returns ~793,230 (~65.7% coverage)**
- [ ] `worldoftaxonomy.com` loads in under 2s
- [ ] Sign-up funnel works end to end (email -> key -> API call)
- [ ] MCP install guide validated in at least one client
- [ ] Sentry receiving events; alerts armed
- [ ] Cloud SQL backups confirmed enabled
- [ ] ToS + privacy + attribution pages exist
- [ ] Ram has signed off on the smoke test

When all of the above are checked, drop a note in the project
channel: "Soft launch ready - opening to first 5 users." Ram
chooses who they are.

## Final notes

- This codebase has a strict "no em-dash" rule enforced by
  `scripts/check_no_em_dash.sh` in CI. Use a regular hyphen.
- All tests must pass on every PR. The test suite uses a
  `test_wot` Postgres schema isolated from production - see
  `tests/conftest.py`.
- TDD is the project norm: red -> green -> refactor.
  See [CONTRIBUTING.md](../../CONTRIBUTING.md).
- Memory files at
  `~/.claude/projects/-Users-ramkotamaraja-Documents-ai-projects-WorldOfTaxonomy/memory/`
  capture longer-running context (auth decisions, deployment plan,
  user preferences). Read those if you're picking up after a long
  break.

Welcome aboard.
