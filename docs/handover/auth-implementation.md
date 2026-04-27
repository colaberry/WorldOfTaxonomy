# Auth Implementation Checklist

> **Companion to** [`portfolio-auth.md`](./portfolio-auth.md). That
> doc explains *what* and *why*; this one is the executable
> *how* - account-by-account, file-by-file, with verification gates
> between phases. Treat each phase as a PR boundary.
>
> **Prerequisites for this work to start**: Cloud Run migration to
> `wot.aixcelerator.ai` is fully landed (PR #1 merged + DNS cut over),
> and the team has provisioned Zitadel Cloud + Permit.io accounts.
> Don't start Phase 1 if either is still pending - the OAuth callback
> URL is part of the Zitadel app config, and changing it post-cutover
> means a manual re-issue of every active session.

## Phase 0 - account provisioning (manual, ~1 hour)

Owner: Ram. Cannot be delegated to Claude (account creation needs
human-in-the-loop email + 2FA).

| Step | Action | Verification |
|---|---|---|
| 0.1 | Create Zitadel Cloud instance. Pick the free tier (25k MAU). | `https://<instance>.zitadel.cloud/ui/console` loads. |
| 0.2 | **OPTIONAL (paid plan only).** Add custom domain `auth.aixcelerator.ai`. Verify the CNAME, request the cert. Skip on free tier; default `<instance>.zitadel.cloud` URL works fine. See "Free tier vs custom domain" below. | Cert status `active` in Zitadel Console > Settings > Domains. |
| 0.3 | Create a Project named `aixcelerator-portfolio`. | Visible in Console > Projects. |
| 0.4 | Inside the project, create a Web Application named `WorldOfTaxonomy`. Authentication method: PKCE. Redirect URI: `https://worldoftaxonomy.com/auth/callback`. Post-logout: `https://worldoftaxonomy.com`. | Application detail page shows the Client ID. |
| 0.5 | Add social IdPs: GitHub, Google, LinkedIn. Use the existing OAuth client IDs from `OAUTH_PRODUCTION_SETUP.md` (no new app registrations - reuse). | Each IdP shows a green check on Console > Settings > Identity Providers. |
| 0.6 | Create a Service User `wot-backend-introspection` for token introspection. Generate a Personal Access Token. | PAT copied to GCP Secret Manager as `zitadel-introspect-pat`. |
| 0.7 | Create Permit.io account. Create an Environment named `prod`. Generate a Project API Key. | Key visible in Permit.io Console > Settings > API Keys. |
| 0.8 | Store secrets in GCP Secret Manager: `zitadel-issuer`, `zitadel-client-id`, `zitadel-introspect-pat`, `permit-api-key`, `permit-pdp-url`. | `gcloud secrets versions access latest --secret=...` returns each. |

Output of Phase 0: a `secrets.txt` Ram keeps in 1Password with the
Client ID, Issuer URL, JWKS URL, and Permit.io project ID. Phase 1
needs all of these.

### Free tier vs custom domain (start free, upgrade later)

Custom domain (step 0.2) is a paid Zitadel feature. The free tier
(25k MAU, all core auth features) works without it. Default
behavior: use the auto-generated `<instance>.zitadel.cloud` URL
everywhere a custom domain would have gone.

What changes when you skip 0.2:

- `ZITADEL_ISSUER` env var becomes
  `https://<instance>.zitadel.cloud` (not `auth.aixcelerator.ai`).
- Users see the Zitadel-owned domain in the address bar for the
  ~2 seconds between clicking "Sign in" and landing back on
  `worldoftaxonomy.com`. Cosmetic; most users never notice.
- The OIDC callback URL registered with social IdPs (GitHub /
  Google / LinkedIn) becomes
  `https://<instance>.zitadel.cloud/ui/login/login/externalidp/callback`.
- The redirect URI you register inside the Zitadel Web App is
  unchanged: `https://worldoftaxonomy.com/auth/callback`. Your own
  domain stays your own domain.

What it costs:

- **Cross-product cookie sharing is harder.** With
  `auth.aixcelerator.ai` you can scope the JWT cookie to the
  `.aixcelerator.ai` apex and share login state across WoT, WoO,
  WoUC, WoA. Without the custom domain you still have SSO at the
  Zitadel session layer (one login covers every product), but each
  product does its own redirect-and-callback dance. Fine while only
  WoT is live; matters when WoO ships.

When to upgrade:

1. **First sibling product launches.** Cross-product cookie
   sharing matters here.
2. **First enterprise prospect asks for SAML.** SAML and custom
   domain are typically bundled in the same paid tier.
3. **MAU approaches 25k.** Until then, free is fine.

The eventual migration:

- Add the custom domain following step 0.2.
- Update `ZITADEL_ISSUER` and `NEXT_PUBLIC_ZITADEL_ISSUER` env vars
  in prod + staging.
- Update the redirect URLs registered with each social IdP
  (GitHub / Google / LinkedIn console edits).
- Every JWT issued before the cutover becomes invalid (`iss` claim
  mismatch). Users get logged out and re-authenticate. One-time
  inconvenience; schedule for a low-traffic window.
- No code change beyond the env var swap.

About 1 hour of work plus one cycle of "everyone re-logs in." Not
painful, just deliberate.

## Developer key model (centralized, scoped, portable)

Zitadel handles **end-user identity** (logging into a dashboard,
signing in with Google, MFA, SAML). It is not the right home for
**developer API keys** — the long-lived bearer tokens devs paste
into `.env` files, MCP configs, and CI runners. Those live in their
own subsystem. This section locks in three architecture decisions
that affect Phase 2 schema, Phase 3 frontend, and the eventual
portfolio extraction.

### Decision 1: one developer account spans the portfolio

A single `app_user` row covers WoT, WoO, WoUC, WoA. Developers see
one signup, one dashboard, one billing relationship. The schema
deliberately does **not** carry a `product_id` column on
`app_user` or `api_key`; product entitlement is expressed through
key scopes (decision 2). This is the same pattern as a Stripe
account (one customer, multiple restricted keys per product) or an
AWS account (one root, scoped IAM access keys).

Sign-up at `/developers` creates the portfolio account regardless
of which product the developer arrived from. The flow does not
change as new products launch; only the available scope options
expand.

### Decision 2: keys carry an array of scopes

```sql
CREATE TABLE api_key (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES app_user(id),
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,                  -- prefix-indexed lookup
    name TEXT,                                 -- "MCP on laptop", "CI runner"
    scopes TEXT[] NOT NULL,                    -- e.g. ['wot:read','wot:export']
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,                    -- optional TTL
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_key_prefix ON api_key (key_prefix)
    WHERE revoked_at IS NULL;
```

Scopes are formatted `<product>:<action>`:

| Scope         | Meaning |
|---|---|
| `wot:read`    | Read taxonomy systems, nodes, equivalences |
| `wot:list`    | List endpoints (search, browse) |
| `wot:export`  | Bulk crosswalk / equivalence dumps (pro tier) |
| `wot:classify`| Submit text to /classify endpoint |
| `wot:admin`   | Admin-only endpoints |
| `woo:*`       | Same shape on WorldOfOntology when it ships |
| `wouc:*`      | Same shape on WorldOfUseCases |
| `woa:*`       | Same shape on WorldOfAgents |

A developer can request whichever combination they need:

- **Maximum convenience**: one key with `['wot:*','woo:*','wouc:*','woa:*']`. Works everywhere.
- **Minimum blast radius**: separate keys per product, e.g., one with `['wot:read','wot:list']`, another with `['woo:read']`. Compromise of one only affects that product.
- **Compliance-driven isolation**: developers whose internal rules require strict separation use product-scoped keys. The schema and audit log treat them as fully independent credentials; rotating, revoking, or auditing one has no effect on others. From the developer's perspective they look like four separate API keys, even though one `app_user` row owns them all.

### Decision 3: the key prefix encodes the scope

Stripe uses `sk_live_*` (live secret) vs `rk_live_*` (restricted live)
vs `pk_live_*` (publishable). GitHub uses `ghp_*` for personal,
`gho_*` for OAuth, `ghs_*` for server. The prefix is a visual
signal that helps with leak detection, log auditing, and
"why-is-this-key-where" investigations.

We follow the same pattern, derived from the scope at issuance:

| Scope contents | Prefix | Example |
|---|---|---|
| Single product, all actions on that product | `wot_`, `woo_`, `wouc_`, `woa_` | `wot_a3f2c5d9...x4z1` |
| Single product, restricted actions | `rwot_`, `rwoo_`, etc. | `rwot_a3f2c5...x4z1` |
| Multiple products | `aix_` | `aix_a3f2c5d9...x4z1` |

Three reasons this matters more than a flat `aix_` everywhere:

1. **Leak triage.** A `wot_` key in a public commit tells the
   secret-scanning team it only affects WoT. A flat `aix_` would
   force "assume worst case, revoke all access until investigated."
2. **Misconfiguration spotting.** A reviewer scanning `.env.production`
   for "the WoT key" greps `wot_` and finds it. With universal
   prefixes they have to look up the key in the dashboard.
3. **Industry expectation.** Developers who have used Stripe,
   GitHub, or AWS keys read prefixes as signals. Following the
   pattern makes WoT feel professional.

The prefix is computed at issuance time from the requested scopes;
it is not a separate user choice. If you ask for `['wot:read']`,
you get `wot_` (or `rwot_` if it's a strict subset of full WoT).
If you ask for cross-product, you get `aix_`.

### Decision 4: build inside WoT now, extract before WoO ships

The keys subsystem is small enough to build inside the WoT
codebase today (~1.5 days, see Phase 6 below). When WoO is 2-4
weeks from launch, extract it to a standalone service at
`developer.aixcelerator.ai` with its own Postgres database
(~2 days migration). WoT and WoO both call the central service
to validate keys; each caches per-key results for 60 seconds to
avoid round-tripping every request.

The portable design above is the contract that survives extraction:

- Tables move databases, schema does not change.
- Validation interface goes from "local SQL lookup" to "HTTP
  `POST /v1/keys/validate { prefix, key, required_scope }`" — same
  inputs, same outputs.
- Migration script copies `app_user` and `api_key` rows once;
  during cutover both WoT and the new central service accept
  validations from either source for ~24 hours.

This avoids two anti-patterns:

- Building a centralized service before there is a second consumer
  (you guess the wrong abstractions).
- Designing keys product-scoped from day 1 and rebuilding the auth
  surface when the second product arrives.

### Phase 6 - developer key issuance and lifecycle (1 PR, ~1.5 days)

This phase ships the user-facing key system. Independent of the
Zitadel migration; can ship before, during, or after Phase 1-5.

Files added:

- `world_of_taxonomy/auth/keys.py` - issuance, hashing, scope check.
- `world_of_taxonomy/auth/magic_link.py` - one-time-token email auth
  for `/developers/keys` (no password, same pattern as Vercel /
  Linear / Notion sign-in).
- `world_of_taxonomy/api/routers/developers.py` - `/api/v1/keys`
  CRUD endpoints, magic-link routes.
- `frontend/src/app/developers/page.tsx` - landing + signup.
- `frontend/src/app/developers/keys/page.tsx` - list / create / revoke.
- `frontend/src/app/auth/magic/page.tsx` - magic-link callback.

Files changed:

- `world_of_taxonomy/schema_auth.sql` - add scope/expiry/audit columns.
- `world_of_taxonomy/api/middleware.py` - validate keys with scope
  check; on 401 / 429 return JSON pointing at `/developers`.
- `world_of_taxonomy/api/deps.py` - new `require_scope("wot:read")`
  dependency factory. Replaces ad-hoc auth checks per route.

Email integration:

- Resend (or Postmark / SES) account, transactional templates:
  - "Your WorldOfTaxonomy API key" - issued on signup
  - "Sign in to manage your keys" - magic link
  - "Key wot_xxx... was just revoked" - revocation receipt
  - "Key expires in 14 days" - rotation reminder
- API key: `RESEND_API_KEY` in GCP Secret Manager.

Verification gate:

- `pytest tests/test_keys.py -v` covers: prefix derivation, scope
  validation, revocation, expiry, magic-link round-trip.
- Manual: signup at `/developers` -> key arrives in inbox -> key
  works on `/api/v1/systems/naics_2022` -> revoke from dashboard ->
  key returns 401 on next call within ~2 seconds (cache TTL).
- Anonymous calls hitting protected endpoints return:
  ```json
  {
    "error": "missing_api_key",
    "message": "API key required. Get a free key at https://worldoftaxonomy.com/developers",
    "anonymous_rate_limit": "30 req/min on public reads"
  }
  ```
  with `WWW-Authenticate: ApiKey` and a `Link: <...>; rel="signup"` header.

### Phase 7 - extract to developer.aixcelerator.ai (1 PR, ~2 days, do this when WoO is in flight)

Triggered by: WoO launch <= 4 weeks away, or third-party developer
asks for a single key across products, whichever comes first.

Steps:

1. Create new repo `aixcelerator-developer` (FastAPI + Next.js).
   Lift `world_of_taxonomy/auth/keys.py` and the `/developers`
   frontend pages out of WoT into the new repo. Code is
   substantially the same; only the package path changes.
2. Provision Postgres for the new service. Define migration
   `0001_initial.sql` that creates `app_user` and `api_key` tables
   with the same shape WoT has.
3. Deploy to Cloud Run at `developer.aixcelerator.ai`.
4. Add `POST /v1/keys/validate` endpoint that takes `{ prefix, key,
   required_scope }` and returns `{ allow: bool, user_id, key_id, scopes }`.
5. In WoT, replace the local DB lookup in `world_of_taxonomy/api/middleware.py`
   with an HTTP call to the central service. Cache the result per
   key for 60 seconds (in-process LRU; do not use Redis until usage
   patterns warrant it).
6. Migrate existing WoT keys: copy `app_user` + `api_key` rows from
   WoT's database into the central database, preserving UUIDs.
   Do this during a maintenance window with WoT's auth in
   read-only-cache mode (validate against in-memory cache only,
   reject revocations) for ~5 minutes during the copy.
7. Cutover env var: `KEY_SERVICE_URL=https://developer.aixcelerator.ai`.
8. Watch for 48 hours. If anything breaks, rollback is a single env
   var revert; the local WoT keys table remains as a safety net for
   one full release cycle, then drops in a follow-up PR.

What WoO does on day 1: clones WoT's middleware integration, sets
its own `KEY_SERVICE_URL` to the same central service, defines its
own scopes (`woo:read`, `woo:export`, etc.) inside the central
scope registry. Estimated 4 hours, not 4 days.

## Phase 1 - backend Zitadel verification (1 PR, ~1 day)

**Goal**: every API request that today calls
`get_current_user(token)` and validates against the local HS256
secret instead validates against Zitadel's RS256 JWKS. Local password
auth still works behind a kill-switch.

Files added:

- `world_of_taxonomy/auth/zitadel.py` - JWKS-cached verifier.
- `world_of_taxonomy/auth/__init__.py` - exports `verify_zitadel_jwt`.

Files changed:

- `world_of_taxonomy/api/deps.py` - `get_current_user` branches on
  `AUTH_MODE` env var: `local` (current bcrypt + HS256) or `zitadel`.
- `world_of_taxonomy/api/app.py` - lifespan handler instantiates the
  JWKS client once.
- `requirements.txt` - add `python-jose[cryptography]>=3.3.0` (already
  present? verify).
- `.env.example` - add `AUTH_MODE`, `ZITADEL_ISSUER`, `ZITADEL_CLIENT_ID`.
- `world_of_taxonomy/__main__.py` (CLI `serve` command) - log the
  active `AUTH_MODE` at startup.

Step-by-step:

1. Create `world_of_taxonomy/auth/zitadel.py` with:
   - `_JWKSCache` (TTL ~10 minutes, refreshes on KeyError).
   - `verify_zitadel_jwt(token: str) -> dict` returning the decoded
     claims dict, raising `HTTPException(401)` on any failure.
   - Validate `iss == ZITADEL_ISSUER`, `aud` contains
     `ZITADEL_CLIENT_ID`, `exp` not past, `nbf` not future.
2. Add `tests/test_zitadel_verifier.py` covering:
   - Valid token (mint with a test RSA key, hand the public key to the
     verifier as a fixture).
   - Expired token -> 401.
   - Wrong issuer -> 401.
   - Wrong audience -> 401.
   - Tampered signature -> 401.
3. Patch `world_of_taxonomy/api/deps.py::get_current_user` to dispatch
   on `os.environ.get("AUTH_MODE", "local")`. Default stays `local`
   so this PR is a no-op until someone flips the env var.
4. Add CI matrix: run the existing API contract tests once with
   `AUTH_MODE=local` (current) and once with a faked Zitadel issuer
   (cassette-style fixture) to prove both paths stay green.

Verification gate:

- `python3 -m pytest tests/ -v` passes.
- `AUTH_MODE=zitadel ZITADEL_ISSUER=... uvicorn ...` boots and
  rejects requests with the *old* HS256 token (proves the new path is
  active).
- `AUTH_MODE=local` boot still accepts the existing bcrypt logins
  (proves the kill-switch works).

## Phase 2 - schema migration (1 PR, ~half a day)

**Goal**: `app_user` rows can store the Zitadel `sub` and link to
existing accounts on next login by email.

Files added:

- `world_of_taxonomy/migrations/0001_add_zitadel_sub.sql`.

Files changed:

- `world_of_taxonomy/schema_auth.sql` - mirrors the new column.
- `tests/conftest.py` - applies the migration to the `test_wot` schema.

Migration:

```sql
ALTER TABLE app_user
    ADD COLUMN zitadel_sub TEXT UNIQUE;
CREATE INDEX IF NOT EXISTS idx_app_user_zitadel_sub
    ON app_user (zitadel_sub) WHERE zitadel_sub IS NOT NULL;
```

Linker logic added to `get_current_user` (zitadel branch only):

1. Decode JWT, extract `sub` and `email`.
2. `SELECT id FROM app_user WHERE zitadel_sub = $1` - hot path.
3. On miss: `SELECT id FROM app_user WHERE email = $2 AND zitadel_sub IS NULL`.
4. If found: `UPDATE app_user SET zitadel_sub = $1 WHERE id = $3`.
5. If miss again: insert new row with `email`, `zitadel_sub`,
   `created_at = NOW()`. No password column populated.

Verification gate:

- `python3 -m pytest tests/test_auth.py -v` passes against the migrated
  schema.
- Running the migration on a snapshot of prod (in a scratch DB) leaves
  every existing user row untouched (`zitadel_sub IS NULL` for all).

## Phase 3 - frontend cutover (1 PR, ~1 day)

**Goal**: `/login` and `/register` pages redirect to Zitadel; the
return path lands the user already authenticated; the API key
dashboard at `/account/api-keys` keeps working.

Files added:

- `frontend/src/app/auth/callback/page.tsx` - PKCE callback handler
  (state + code verifier from sessionStorage).
- `frontend/src/lib/zitadel.ts` - thin client wrapper around the OIDC
  authorization endpoint.

Files changed:

- `frontend/src/app/login/page.tsx` - replaced with a redirect to
  Zitadel's hosted login.
- `frontend/src/app/register/page.tsx` - same redirect, with
  `prompt=create` query param to land on the registration screen.
- `frontend/src/app/account/page.tsx` - the profile section becomes a
  deep-link to Zitadel's user profile; the API keys section stays as
  is (Phase 4 enhances it).
- `frontend/.env.example` - `NEXT_PUBLIC_ZITADEL_ISSUER`,
  `NEXT_PUBLIC_ZITADEL_CLIENT_ID`.

Step-by-step:

1. Implement PKCE in `frontend/src/lib/zitadel.ts`: generate
   `code_verifier` (`crypto.getRandomValues` + base64url),
   `code_challenge = SHA-256(verifier)`, redirect to
   `${issuer}/oauth/v2/authorize?...`.
2. The `/auth/callback` page reads `code` and `state` from query
   params, exchanges via `POST /oauth/v2/token`, stores the resulting
   JWT in an httpOnly cookie via a new `/api/v1/auth/zitadel-callback`
   backend route (so the JS layer never touches the token).
3. Backend route `world_of_taxonomy/api/routers/auth.py` adds
   `POST /auth/zitadel-callback`: takes the auth code, exchanges via
   Zitadel's token endpoint (using the introspection PAT for the
   client secret), sets the cookie, returns the user record.
4. Drop the legacy `/login` / `/register` form components after the
   feature flag flips (Phase 5).
5. Manually verify the loop: visit `/login` -> Zitadel hosted login
   -> social provider -> back to `worldoftaxonomy.com` -> dashboard
   shows the logged-in state. Test on incognito + Safari + a real
   mobile.

Verification gate:

- `npm run build` clean (no TS errors).
- `playwright test tests/e2e/auth.spec.ts` (new) covers the redirect,
  callback, logged-in state, and logout. Use Zitadel's *test* tenant
  for E2E; never the prod IdP.

## Phase 4 - Permit.io authorization (1 PR, ~2 days)

**Goal**: every protected endpoint calls `permit.check()` for any
operation whose answer depends on more than "authenticated y/n."
Coarse rate-limit tiers stay on the Zitadel claim, untouched.

Files added:

- `world_of_taxonomy/authz/permit.py` - thin wrapper around the
  Permit.io Python SDK; exposes `check(user, action, resource, **ctx)`.
- `world_of_taxonomy/authz/__init__.py` - exports `permit_check`.
- `world_of_taxonomy/migrations/0002_add_org_id_to_app_user.sql` -
  optional, only if Phase 0 step 0.4 created Zitadel orgs and we want
  to mirror them locally (no schema change needed if we read org from
  the JWT claim each request).

Files changed:

- `world_of_taxonomy/api/deps.py` - exports a `require_permit(action,
  resource_type)` FastAPI dependency factory.
- `world_of_taxonomy/api/routers/equivalences.py` and
  `world_of_taxonomy/api/routers/nodes.py` - add
  `Depends(require_permit("export", "equivalence"))` to bulk-export
  routes; add `require_permit("admin", "system")` to admin routes.
- `requirements.txt` - add `permit>=2.0`.

Bootstrap policies (committed in `permit/policies/` and synced via
Permit.io GitOps integration):

| Policy ID | Subject | Action | Resource | Condition |
|---|---|---|---|---|
| `anon-read-public` | anonymous | `read` | `system` | `system.public == true` |
| `auth-read-list` | authenticated | `read,list` | `system,node,equivalence` | none |
| `pro-bulk-export` | tier=`pro` | `export` | `equivalence` | none |
| `enterprise-cross-org` | role=`enterprise-admin` | `read` | `system` | `system.org_id IN user.linked_orgs` |
| `admin-only` | role=`admin` | `admin` | `*` | none |
| `agent-delegated` | role=`agent`, has-delegation-from(user) | `classify` | `node` | `node.system_id IN delegation.scopes` |

Verification gate:

- `python3 -m pytest tests/test_authz_permit.py -v` (new file with
  ~10 unit tests + 3 integration tests against a Permit.io test
  environment).
- A bulk-export call from a `free`-tier token returns 403; same call
  from a `pro` token returns 200.
- An admin-only endpoint returns 403 for a regular user, 200 for an
  admin token.

## Phase 5 - cutover and decommission (1 PR, ~half a day)

**Goal**: flip prod to `AUTH_MODE=zitadel`, monitor for 48 hours,
then delete the legacy auth code in a follow-up.

Step-by-step:

1. Deploy Phase 1-4 to staging with `AUTH_MODE=zitadel`. Run a
   canary for 24 hours. Watch:
   - `wot_authz_decisions_total{decision="deny"}` Prometheus metric -
     should be near-zero outside expected denials.
   - 4xx rate on `/api/v1/*` - should not spike.
   - User support tickets - should stay flat.
2. Flip prod env var: `AUTH_MODE=zitadel`. Restart Cloud Run revision.
3. Monitor for 48 hours. Have the rollback ready (revert env to
   `local`, no schema rollback needed because the column is additive).
4. Follow-up PR: delete `world_of_taxonomy/api/auth/local.py`,
   `bcrypt`-related logic, the `password_hash` column (in a separate
   migration with a deprecation window), and the legacy `/login`,
   `/register` endpoints.

Verification gate:

- 48 hours of green dashboards.
- Zero auth-related support tickets.
- Stripe webhook still updates the `tier` column (proves the
  Zitadel-org -> Stripe-customer mapping survived the cutover).

## Observability hooks (added incrementally per phase)

- **Phase 1**: log every JWKS cache miss + every auth failure with
  reason (`exp`, `aud`, `iss`, `sig`). Surface as
  `wot_auth_failures_total{reason="..."}`.
- **Phase 4**: log every Permit.io decision with latency. Surface as
  `wot_authz_decisions_total{decision="...",resource_type="..."}` and
  `wot_authz_latency_seconds`.
- **Phase 5**: dashboard panel "Auth health" combines auth failure
  rate + authz deny rate + Zitadel availability + Permit.io PDP
  latency. Lives in the existing Grafana board referenced by
  `docs/handover/cicd-deployment.md`.

## What this doc deliberately leaves out

- **Account / billing UI rebuild.** Stripe wiring stays in its own
  doc; this checklist stops at "the Zitadel org ID is the Stripe
  customer key."
- **WoO / WoUC / WoA onboarding.** Each subsequent product follows
  this same checklist, just shorter (Phase 0 reuses the same Zitadel
  instance and Permit.io project; Phase 1-4 are mostly copy-paste of
  the WoT module). Estimated 1-2 days per product.
- **SAML / Enterprise SSO.** Free Zitadel plan does not include SAML.
  When the first enterprise prospect asks, upgrade Zitadel to the
  Pro plan and add a SAML connection per customer through the
  console. No code change needed; SAML logins emit the same JWT.
- **MFA enforcement.** Configure in Zitadel Console > Settings >
  Login Policy. Out of scope for this checklist.
- **Audit log retention.** Zitadel keeps its own audit log; product
  access logs stay in Cloud Logging. A unified audit view is a
  separate project.

## Rollback playbook

For each phase, the rollback is one revert away:

| Phase | Rollback action | Effect |
|---|---|---|
| 1 | Set `AUTH_MODE=local` | Backend rejects Zitadel tokens, accepts legacy bcrypt + HS256 again. |
| 2 | None needed | The new column is additive; leaving `zitadel_sub` populated does not break local auth. |
| 3 | Roll back the frontend deploy | Old login / register pages return; no backend change required. |
| 4 | Remove the `Depends(require_permit(...))` from each route | Authz decisions go back to coarse "authenticated y/n." |
| 5 | Set `AUTH_MODE=local` | Same as Phase 1 rollback. |
| 6 | Disable the `/developers` route + revert middleware to coarse-tier check | API stays available; key issuance pauses. Revoked keys stay revoked (DB-side, no rollback path needed). |
| 7 | `KEY_SERVICE_URL=` (empty) | Middleware falls back to local DB lookup against the original WoT keys table (kept as safety net for one release cycle post-extraction). |

Never roll back by deleting the `app_user.zitadel_sub` column. The
column being populated for some users is harmless; deleting it loses
the link and forces re-onboarding.

## Estimated total effort

- Phase 0: 1 hour (Ram, manual).
- Phase 1: 1 day (Claude Code or contributor).
- Phase 2: half a day.
- Phase 3: 1 day.
- Phase 4: 2 days.
- Phase 5: half a day to flip + 48 hours of monitoring before the
  legacy-code deletion follow-up.
- Phase 6: 1.5 days. Independent of Phase 1-5; can ship before
  Zitadel arrives. **This is the API/MCP gate for launch.**
- Phase 7: 2 days. Triggered by WoO launch <= 4 weeks away or first
  customer asking for cross-product keys.

Wall-clock for the Zitadel migration (Phase 1-5): about a calendar
week with one engineer, fully focused. Worth doing as a single
concentrated push rather than spread over a month - the schema
migration in Phase 2 and the cutover in Phase 5 are easier when
Phase 1 is fresh in everyone's head.

Wall-clock for the developer-key system (Phase 6): 1.5 days, ships
the API/MCP launch gate. Phase 7 (extraction to
`developer.aixcelerator.ai`) is deferred until WoO is in flight; do
not pre-build it.

Recommended sequence if launching WoT before Zitadel migration:

```
Phase 6 (key system in WoT)         -> ships API + MCP gate
[launch WoT publicly]
[customer feedback, validate demand]
Phase 0-5 (Zitadel + Permit.io)     -> when first paying customer or WoO is on the calendar
Phase 7 (extract key service)       -> when WoO is 2-4 weeks from launch
```

Recommended sequence if Zitadel migration ships before WoT goes
public:

```
Phase 6 (key system in WoT)         -> ships first regardless; this is the gate
Phase 0-5 (Zitadel + Permit.io)     -> in parallel or immediately after
Phase 7 (extract key service)       -> deferred to WoO timing
```

Either way, Phase 6 ships first. The key system is the launch
gate; everything else is portfolio prep.
