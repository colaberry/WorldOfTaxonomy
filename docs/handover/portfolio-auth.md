# Portfolio Auth Architecture

> **Status: proposed architecture, not yet implemented.** Zitadel Cloud
> has been chosen as the authentication IdP and Permit.io has been
> chosen as the authorization engine, but neither is provisioned or
> integrated yet. WoT today still uses local bcrypt passwords plus
> HS256 JWTs (see `world_of_taxonomy/api/deps.py`). When the migration
> lands, this doc becomes current-state; until then, treat it as the
> roadmap.

This doc lives in the WorldOfTaxonomy repo because WoT is the first
product to need the integration, but the design is portfolio-wide. It
applies to every product under `aiaccelerator.ai`:

- WorldOfTaxonomy (`worldoftaxonomy.com`)
- WorldOfOntology (planned)
- WorldOfUseCases (planned)
- WorldOfAgents (planned)
- anything else the portfolio adds later

## Goal

One identity across the portfolio. A user signs in once at
`auth.aiaccelerator.ai`, lands back on any World-Of site already logged
in, sees one account page, has one billing relationship, and uses one
set of API keys that work across every product with per-product
entitlements.

## Two layers: authentication and authorization

Portfolio auth is split into two hosted services with strict separation
of concerns:

- **Authentication (who are you?)** - Zitadel Cloud. Identity, login,
  MFA, social, SSO, orgs, roles, PATs.
- **Authorization (what can you do?)** - Permit.io. Fine-grained policy
  decisions: ABAC + ReBAC, policy-as-code via GitOps.

Every product verifies the Zitadel-issued JWT on every request, then
calls `permit.check(user, action, resource)` for any operation whose
answer depends on more than "is the user authenticated at all."
Coarse rate-limit tiers (`free` / `pro` / `enterprise`) stay as claims
on the Zitadel token so the hot path does not round-trip to Permit.io
per request.

## Decision: Zitadel Cloud (authentication)

The central Identity Provider is **Zitadel Cloud**, hosted at
`auth.aiaccelerator.ai`. The decision criteria and the alternatives
considered are captured in [memory](../../../.claude/...). Short version:

| Requirement | Why Zitadel Cloud |
|-------------|-------------------|
| One billing across products | Native org/user hierarchy; Stripe customer = Zitadel org |
| Enterprise SSO (SAML + SCIM) within 12 months | SAML and SCIM on every tier, no per-connection upsell |
| Outsource security | Fully managed; never touch the infrastructure |
| Long-lived API keys for paid tiers | Native Personal Access Tokens, not M2M grants |
| OIDC for all products | Standard OIDC + JWKS; any product in any language integrates |

Rejected alternatives: Auth0 (API-key fit + MAU pricing), Keycloak /
self-hosted Zitadel (ops burden), WorkOS (per-SAML-connection pricing,
weak API-key story), Clerk (SAML is a paid add-on), rolling our own
(permanent maintenance burden).

## Decision: Permit.io (authorization)

The central policy engine is **Permit.io**, a hosted policy-as-a-service
that wraps OPA (for ABAC) and OpenFGA (for ReBAC) behind one SDK and
one management plane. Zitadel answers "who is this?"; Permit.io answers
"can this subject perform this action on this resource, given this
context?"

| Requirement | Why Permit.io |
|-------------|---------------|
| Outsource security (Ram's preference) | Hosted policy-as-a-service; no ops burden |
| ABAC and ReBAC both needed | Wraps OPA (ABAC) and OpenFGA (ReBAC) under one API |
| Multi-language SDKs across product portfolio | First-class Python and TypeScript SDKs; HTTP PDP available for anything else |
| Pairs cleanly with Zitadel | Sync SDK pulls Zitadel users/orgs/roles into Permit.io as subjects |
| Policy-as-code for review and rollback | GitOps integration; policies committed to a repo, not clicked into a UI |
| Generous free tier for pre-revenue stage | 1000 MAU free, reasonable growth pricing |

Rejected alternatives:

- **AuthZed Cloud (SpiceDB)** - excellent at ReBAC, weaker for pure
  ABAC, steeper learning curve. Less relevant when Permit.io already
  wraps ReBAC via OpenFGA.
- **OpenFGA self-hosted** - conflicts with the outsource-security
  preference; ops burden on a security-critical service.
- **Cerbos** - policy-as-code done well, but does not handle ReBAC
  natively; agent-delegation scenarios want ReBAC.
- **Auth0 FGA** - bundled with Auth0; does not help because we did
  not pick Auth0.
- **Build authz in each product** - what we are explicitly avoiding.
  Four products authoring their own authz is four codebases that drift
  apart and four audit surfaces.

### Coarse vs fine-grained checks

| Check | Where |
|-------|-------|
| Is the JWT valid and unexpired? | Backend, JWKS verification (no network call per request once JWKS is cached) |
| Is the user authenticated at all? | Backend, from JWT presence |
| Is the user on the "pro" tier (for rate limits)? | Zitadel claim on token |
| Can this user read a given system? | Permit.io |
| Can this user export bulk crosswalk data for system X? | Permit.io |
| Can this agent classify on behalf of org Y? | Permit.io |
| Can user A share an API key with user B? | Permit.io |

## Architecture

```
    ┌─────────────────────────────────┐      ┌─────────────────────────────────┐
    │  auth.aiaccelerator.ai          │      │  Permit.io (hosted PDP)         │
    │  (Zitadel Cloud)                │      │                                 │
    │                                 │      │  - Policy-as-code (GitOps)      │
    │  - Login, MFA, social, SSO      │      │  - ABAC (OPA) + ReBAC (OpenFGA) │
    │  - Orgs (= Stripe customers)    │      │  - Subjects synced from Zitadel │
    │  - Users, roles, PATs           │      │  - Decision logs                │
    │  - SAML + SCIM for enterprise   │      │                                 │
    └──────────┬──────────────────────┘      └────────────────┬────────────────┘
               │                                              │
               │  1. OIDC, JWKS (authN)                       │  2. permit.check (authZ)
               │                                              │
     ┌─────────┴──────────────────────────────────────────────┴──────────┐
     │                                                                    │
     ▼                                                                    ▼
┌───────────────────┐    ┌───────────────────┐        ┌───────────────────┐
│ worldoftaxonomy   │    │ worldofontology   │        │ worldofagents     │
│                   │    │                   │        │                   │
│ - Web (Next.js)   │    │ - Web             │        │ - Web             │
│ - REST API        │    │ - REST API        │        │ - REST API        │
│ - MCP server      │    │ - MCP server      │        │ - MCP server      │
│                   │    │                   │        │                   │
│ 1. Verify JWT     │    │ 1. Verify JWT     │        │ 1. Verify JWT     │
│    via JWKS       │    │    via JWKS       │        │    via JWKS       │
│ 2. permit.check() │    │ 2. permit.check() │        │ 2. permit.check() │
│    per operation  │    │    per operation  │        │    per operation  │
└─────────┬─────────┘    └─────────┬─────────┘        └─────────┬─────────┘
          │                        │                            │
          │                        ▼                            │
          │              ┌───────────────────┐                  │
          └─────────────▶│ Stripe            │◀─────────────────┘
                         │ customer = Zitadel│
                         │ org; products =   │
                         │ SKUs on subscr.   │
                         └───────────────────┘
```

Every product, every protected request:

1. Redirects unauthenticated web users to `auth.aiaccelerator.ai/login`.
2. On callback, verifies the Zitadel-issued ID token via cached JWKS,
   then mints (or accepts) its own session.
3. Verifies REST/MCP bearer tokens against Zitadel's JWKS (RS256).
4. Accepts Zitadel Personal Access Tokens (long-lived, user-scoped) as
   "API keys" for paid tiers. Tier claim on the token drives rate-limit
   buckets without a Permit.io round-trip.
5. For any operation whose answer depends on org membership, resource
   ownership, enterprise contract terms, or agent delegation, calls
   `permit.check(user, action, resource, context)` and respects the
   allow/deny decision.
6. Products do not author policy locally. Policies live in Permit.io,
   versioned via the GitOps integration, reviewed like code.

## What this changes for WorldOfTaxonomy

WoT currently implements auth itself: bcrypt passwords, HS256 JWT,
three OAuth providers, a `wot_` API-key table. The central-IdP
migration replaces the first three and re-homes the fourth:

| Today (WoT-local) | After migration (Zitadel-backed) |
|-------------------|-----------------------------------|
| `POST /auth/register` + bcrypt | Deleted. Users register at `auth.aiaccelerator.ai`. |
| `POST /auth/login` + HS256 JWT | Deleted. Login happens at Zitadel; backend verifies RS256 JWT via JWKS. |
| `/auth/oauth/{github,google,linkedin}` | Deleted. Social providers are configured once inside Zitadel. |
| `JWT_SECRET` env var | Deleted. Replaced by `ZITADEL_ISSUER` + JWKS URL. |
| `app_user` table | Keep, but add `zitadel_sub` (TEXT, unique). New rows created on first login keyed by `sub`. Existing rows get linked by email on next login. |
| `api_key` table with `wot_...` prefix | Two options: (A) keep the table, continue minting `wot_...` keys, but scope them to a `zitadel_sub` instead of a local user ID. (B) move entirely to Zitadel Personal Access Tokens. **Recommendation: (A)** - it preserves the `wot_...` ergonomics and doesn't force every skills bundle to re-plumb. |
| Rate-limit tier lookup | Unchanged mechanism; `tier` now comes from a claim on the Zitadel token or from the local `app_user.tier` column that Stripe webhooks update. |

## Migration path for WoT

1. **Provision.** Create a Zitadel Cloud instance, point
   `auth.aiaccelerator.ai` at it, register WoT as an OIDC application
   with callback `https://worldoftaxonomy.com/auth/callback`. Import
   GitHub / Google / LinkedIn social providers inside Zitadel (removes
   the per-product provider admin-console work forever).
2. **Backend token verification.** Add a `world_of_taxonomy/auth/zitadel.py`
   module. Rewrite `get_current_user` in `world_of_taxonomy/api/deps.py`
   to verify via the Zitadel JWKS URL (cached, with a JWKSClient).
   Drop `JWT_SECRET`. Keep the existing `DISABLE_AUTH=true` dev bypass.
3. **Schema.** `ALTER TABLE app_user ADD COLUMN zitadel_sub TEXT UNIQUE`.
   Migration script backfills NULL; next-login flow links by email.
   Drop `oauth_provider`, `oauth_provider_id`, and the password columns
   after all users have signed in once (a deprecation window, not an
   immediate drop).
4. **Frontend.** Replace `/login` and `/register` pages with a redirect
   to Zitadel's hosted login. Account page (`/account`) becomes a thin
   shell that iframes or deep-links Zitadel's user profile.
5. **API keys.** Keep minting `wot_...` keys from the dashboard, but
   store the Zitadel `sub` alongside. Nothing changes for the customer.
6. **Stripe wiring.** Stripe customer metadata carries the Zitadel org
   ID. Subscription webhooks update a `tier` column on the org; the
   rate-limit middleware reads from there instead of from the user
   record directly.
7. **Cut over.** Behind a feature flag (`AUTH_MODE=zitadel`), route
   new logins to Zitadel. Once green in staging, flip the flag in prod
   and delete the legacy routes in a follow-up release.

Authz-specific steps (added once authentication is working end-to-end):

8. **Provision Permit.io project.** Create the project (scope decision
   below: one project per product vs. one portfolio-wide project).
   Define resource types (`system`, `node`, `equivalence`, `api_key`,
   `org`, `user`) and actions (`read`, `list`, `write`, `delete`,
   `classify`, `export`, `admin`).
9. **Sync Zitadel to Permit.io.** Use Permit.io's identity sync SDK or
   a Zitadel Actions webhook to mirror user/org/role creation. Subjects
   in Permit.io are keyed by Zitadel `sub`; orgs in Permit.io are keyed
   by Zitadel org ID (same key Stripe uses).
10. **Add the `permit` dependency** in
    `world_of_taxonomy/authz/permit.py` (new module). Initialize the
    Permit client at app startup via the FastAPI lifespan; inject it
    into request handlers as a dependency alongside `get_current_user`
    in `world_of_taxonomy/api/deps.py`.
11. **Replace local authorization checks with `permit.check()`.** WoT's
    current checks are coarse (authenticated vs. anonymous, tier-based
    rate limits); the migration is mostly additive. Start with bulk
    export and admin-only endpoints, then extend to per-resource reads
    once enterprise cross-org sharing lands.
12. **Policy bootstrap.** Write the first 5 to 10 policies via Permit.io
    GitOps: anonymous read on public systems, authenticated read/list,
    pro-tier bulk export, enterprise cross-org sharing, admin
    operations, agent delegation on behalf of a user.
13. **Observability.** Surface Permit.io decision logs as a Prometheus
    metric family in the existing setup:
    `wot_authz_decisions_total{decision="allow|deny",resource_type="..."}`.
    Keep per-request rate-limit counters untouched in
    `world_of_taxonomy/api/middleware.py`; they remain driven by the
    Zitadel tier claim, not by Permit.io.

Expect three to five focused days for the authentication layer, plus
another two to three days for the authorization layer wiring and
policy bootstrap. Every subsequent World-Of product is one to two days
because the pattern is already worn in.

## What this does *not* cover

- Which Zitadel Cloud plan to pick. Start on the free tier; the paid
  plan becomes relevant when MAU or SAML requirements cross the
  threshold.
- Billing implementation. Stripe wiring is a separate doc; this one
  stops at "org = Stripe customer."
- Secrets management for the Zitadel machine-user credentials (the
  client secret each product uses to introspect tokens). Default to
  GCP Secret Manager referenced from Cloud Run env vars, consistent
  with the rest of the deploy stack.
- Audit logging at the portfolio level. Zitadel writes its own; each
  product still writes its own access log. A unified log view can
  come later if needed.

## Decisions locked in (2026-04-18)

- **Domain standardization.** Portfolio standardizes on
  `aiaccelerator.ai`. WoT's API moves from `wot.aixcelerator.app` to
  `wot.aiaccelerator.ai`. Auth lives at `auth.aiaccelerator.ai`. The
  migration is a CORS + OAuth-callback + docs-URL update, not a rebuild.
- **Permit.io project scope.** One portfolio-wide Permit.io project.
  Motivation: cross-product policies (e.g., "enterprise seat on WoT
  grants read-only on WoO") are the whole point of a central authz
  layer. Revisit only if the policy surface grows large enough to
  warrant per-product isolation.
- **Authz rollout sequencing.** Ship Zitadel migration first, keep
  current coarse checks, then layer Permit.io on top once auth is
  stable in prod. No simultaneous cutover.

## Open questions Ram still has to decide

1. **When to migrate to Zitadel.** Before the first paying customer
   (cheap) or after launch (unblocks launch, harder to retrofit). The
   current WoT auth works; this is not launch-blocking.
2. **Skip the per-product OAuth setup?** The existing
   `OAUTH_PRODUCTION_SETUP.md` wires GitHub / Google / LinkedIn OAuth
   apps directly into WoT. If Zitadel comes soon, that whole setup is
   throwaway. Tied to question 1.
