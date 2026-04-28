# Phase 6 (Developer API Keys) - Session Handover Prompt

> **How to use this:** Open a fresh Claude Code session inside this
> repo and paste the entire block below (everything between the
> `---PROMPT---` markers) as your first message. The new session
> will pick up with full context and can start writing code
> immediately.

```
---PROMPT---

I'm starting a new session to implement Phase 6 of the auth roadmap:
the developer API key system that gates the WorldOfTaxonomy public API
and MCP server. Soft launch is now live; this is the next blocker on
the public-launch critical path.

## Required reading (in this order, before writing any code)

1. `CLAUDE.md` - project tour, schema, Python version notes (system
   `/usr/bin/python3` 3.9, NOT homebrew 3.14).
2. `docs/handover/auth-implementation.md` - the canonical Phase 6
   specification. Read all of "Developer key model" section + Phase 6
   in full. Sections to internalize:
   - Decision 1: one developer account spans portfolio
   - Decision 2: keys carry an array of scopes
   - Decision 3: prefix encodes scope (wot_/rwot_/aix_)
   - Decision 4: build inside WoT now, extract pre-WoO
   - "Multi-user from the same company domain" (org bucketing)
   - "Phase 6 - developer key issuance and lifecycle"
3. `docs/handover/portfolio-auth.md` - design rationale.
4. `world_of_taxonomy/schema_auth.sql` - current schema (will need
   migrating).
5. `world_of_taxonomy/api/routers/auth.py` - existing auth router
   (registration / login / keys CRUD with password+JWT).
6. `world_of_taxonomy/api/middleware.py` - existing rate limiter
   (per-user, needs to become per-org).
7. `world_of_taxonomy/api/deps.py` - `get_current_user`.
8. `world_of_taxonomy/mcp/server.py` - MCP server (currently no
   `WOT_API_KEY` handling; needs to read env and send Authorization
   header).
9. `tests/test_auth.py` - existing auth tests.

## Memory files to read

The user keeps persistent decisions in
`~/.claude/projects/-Users-ramkotamaraja-Documents-ai-projects-WorldOfTaxonomy/memory/`.
Read these specifically:

- `project_developer_keys.md` - centralized keys at
  developer.aixcelerator.ai, prefix scheme wot_/rwot_/aix_,
  Path B sequencing (build in WoT, extract pre-WoO).
- `project_org_throttling.md` - rate limits at org level always;
  corp-domain shares pool, free-email gets personal org. **Closes
  per-user-times-N bypass; do not regress this.**
- `project_classify_gate.md` - email-only gate on `/classify` now;
  swap to Zitadel later. Phase 6 should leave the `/classify` flow
  alone.
- `project_monetization_strategy.md` - free / pro / enterprise tiers.
- `project_zitadel_free_tier.md` - Zitadel custom domain deferred;
  Phase 6 must coexist later via the linker pattern.
- `project_auth_decision.md` and `project_authz_decision.md` for
  Zitadel + Permit.io decisions.
- `feedback_outsource_security.md` - default to hosted services.

## What's already done (don't redo)

- Basic `app_user`, `api_key`, `usage_log` tables in
  `schema_auth.sql`. Will need migration, NOT replacement.
- Registration with email + password + bcrypt + JWT.
- `POST /api/v1/auth/keys` mints a `wot_<32hex>` key, bcrypt-hashes
  it, prefix-indexes for lookup. Functional but unscoped and
  per-user-tier-only.
- Rate limit middleware with anonymous=30/min, authenticated=1000/min
  buckets.
- Soft launch is live. Don't break running production.

## What you must implement (Phase 6 deliverables)

Schema migrations:

1. Add `org` table with `kind` ('corporate' | 'personal'),
   `domain UNIQUE`, `tier`, `rate_limit_pool_per_minute`,
   `stripe_customer_id`, `zitadel_org_id`.
2. Add `app_user.org_id NOT NULL` (backfill existing users into
   per-user personal orgs by email before applying NOT NULL),
   `app_user.role`, `app_user.zitadel_sub` (NULL until Phase 2).
3. Add `api_key.scopes TEXT[]` (e.g. `['wot:read','wot:export']`),
   `api_key.revoked_at`, `api_key.revoked_reason`,
   `api_key.expires_at`, `api_key.last_used_at`, `api_key.name`.
4. Provide an Alembic migration in `migrations/`. The user runs
   migrations locally (`wot-postgres` Docker container) and on
   Cloud SQL via gcloud sql import.

Backend code:

1. `world_of_taxonomy/auth/keys.py` - issuance, scope check, prefix
   derivation (wot_/rwot_/aix_).
2. `world_of_taxonomy/auth/magic_link.py` - one-time email-token
   sign-in (no password). Token TTL 15 min.
3. `world_of_taxonomy/auth/email.py` - thin Resend (or
   Postmark/SES) wrapper. Use `RESEND_API_KEY` from environment.
   Default sender: `noreply@aixcelerator.ai`.
4. `world_of_taxonomy/api/routers/developers.py` - new router for
   `/api/v1/keys/*` (CRUD with scope check), magic-link routes
   (`/auth/magic-link`, `/auth/magic`), and key validation hook for
   middleware.
5. Update `world_of_taxonomy/api/middleware.py` to key the rate
   limiter on `org_id`, NEVER on `user_id`.
6. Update `world_of_taxonomy/api/deps.py` with a
   `require_scope(scope: str)` FastAPI dependency factory.
7. Update `world_of_taxonomy/mcp/server.py` to read `WOT_API_KEY`
   from environment, send `Authorization: Bearer <key>` on every
   API call, fail clearly if not set.

Frontend:

1. `frontend/src/app/developers/page.tsx` - landing page + email
   signup form.
2. `frontend/src/app/developers/keys/page.tsx` - list / create /
   revoke keys (after magic-link sign-in).
3. `frontend/src/app/auth/magic/page.tsx` - magic-link callback
   handler (POSTs token to `/auth/magic-callback`, sets cookie).

Helpful 401 / 429 responses:

- 401 returns JSON with `error: "missing_api_key"`, link to
  `/developers`, plus `WWW-Authenticate: ApiKey` and
  `Link: <https://worldoftaxonomy.com/developers>; rel="signup"`
  headers.
- 429 returns JSON with the upgrade-to-pro pointer.

Email templates (Resend):

- "Your WorldOfTaxonomy API key" (issued on signup)
- "Sign in to manage your keys" (magic-link)
- "Key wot_xxx... was just revoked" (revocation receipt)

## Constraints (project-wide, non-negotiable)

- **TDD**: red -> green -> refactor. Write the failing test first.
  Run it red. Then write the minimum code to pass. Refactor with
  tests green. See `CONTRIBUTING.md`.
- **No em-dashes anywhere** (code, docs, commits). CI gate via
  `scripts/check_no_em_dash.sh`. Use a regular hyphen.
- **Test isolation**: `tests/conftest.py` creates a `test_wot`
  Postgres schema per session and tears it down. Never run tests
  against `public` schema.
- **Python**: use `/usr/bin/python3` (system 3.9.6 with deps).
  Homebrew `python3` is 3.14 and lacks deps. The Postgres lives in
  the `wot-postgres` Docker container.
- **Auth coexistence**: design must allow Zitadel migration later
  via the linker pattern in Phase 2. Specifically: keep
  `app_user.email` `UNIQUE NOT NULL`, add `zitadel_sub` column NULL
  by default, never assume password presence.
- **Security**: outsource where possible (Resend for email, GCP
  Secret Manager for keys). No rolling-our-own crypto.
- **Don't break the live API**: existing `/api/v1/auth/*` routes
  must continue to work during migration. Old `wot_<32hex>` keys in
  use today should keep working (backfill to scope=`['wot:*']` and
  per-user personal org).

## Verification gates (must be green before merge)

Before opening a PR, all of these must pass:

- `pytest tests/ -v` (all tests, including new Phase 6 ones)
- `bash scripts/check_no_em_dash.sh world_of_taxonomy/ tests/ frontend/src/ *.md docs/handover/*.md`
- Manual end-to-end smoke:
  1. POST email at `/developers` -> magic link arrives at email
  2. Click link -> redirected to `/developers/keys`, cookie set
  3. Click "Generate key" -> key shown ONCE in UI
  4. `curl -H "Authorization: Bearer <key>" /api/v1/systems/naics_2022`
     returns 200
  5. Anon `curl /api/v1/systems` returns 200 but only public scope
     reads
  6. Anon hits export endpoint -> 401 with helpful JSON pointing at
     `/developers`
  7. Two users at `@acme.com` share a 1,000 req/min pool (rate
     limit at the org level)
  8. Single Gmail user gets a personal org with 1,000 req/min pool
- MCP smoke: `WOT_API_KEY=wot_... uvx worldoftaxonomy-mcp` works in
  Claude Desktop; missing-key startup prints actionable error.

## Where to start (first concrete actions)

1. Read all the files listed in "Required reading" above. Do not
   skip; the design has nuances (especially in
   `auth-implementation.md`).
2. Read the memory files. Confirm understanding by summarizing each
   in one sentence.
3. Run the existing tests to confirm baseline:
   `/usr/bin/python3 -m pytest tests/test_auth.py -v`.
4. Inspect the live schema to ensure understanding:
   `docker exec wot-postgres psql -U wot -d worldoftaxanomy -c "\d app_user; \d api_key;"`.
5. Propose the TDD plan: list the failing tests you'll write first,
   in order, with a one-line description of each. Get user approval
   on the test plan before writing implementation.
6. Write the first failing test (likely the schema migration test).
   Make it red. Then write the minimum to pass. Repeat.
7. Open a draft PR early so the user can see incremental progress.

## What you should ask the user before deciding

- **Email service**: Resend vs Postmark vs SES. Default to Resend
  unless told otherwise.
- **MCP package distribution**: npm `@worldoftaxonomy/mcp` vs PyPI
  `worldoftaxonomy-mcp`. Affects the install snippet in
  `wiki/mcp-setup.md`.
- **Free-email-domain list**: hardcode a small list (gmail, yahoo,
  hotmail, proton, icloud, outlook, fastmail) or pull from a public
  dataset. Default to hardcoded list.
- **Whether to ship Phase 6.5 (SSO option) in the same PR**: depends
  on Zitadel readiness. Default: ship Phase 6 alone, defer 6.5.

## How to wrap up

When Phase 6 is merged and the manual smoke tests pass, update:

- `docs/handover/launch-checklist.md` checkbox under
  "Soft-launch critical path -> 3. Phase 6 developer-key issuance system".
- Add a memory file
  `project_phase6_complete.md` summarizing what shipped, with the
  date and PR numbers.

Good luck. The doc has every detail; trust the spec.

---PROMPT---
```

## How to use it

1. Open a new Claude Code session in this repo (or a fresh terminal
   running `claude`).
2. Paste the entire block above (between the `---PROMPT---` markers)
   as your first message.
3. Wait for the agent to read everything and propose its TDD plan.
4. Approve or redirect, then let it go.

If you want to send the deployment dev to do this instead of doing
it yourself, send them this URL:

```
https://github.com/colaberry/WorldOfTaxonomy/blob/main/docs/handover/phase6-api-keys-prompt.md
```

They click the URL, copy the prompt, paste into their Claude Code,
and they're off.
