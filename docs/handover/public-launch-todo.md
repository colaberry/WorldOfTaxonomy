# Public-launch TODO

Six items to land before the public HN/X push. **Not** required for soft
launch; the soft-launch gate is in
[launch-checklist.md](./launch-checklist.md). Each item links to its
detail location and lists the rough effort + the unblock condition.

| # | Item | Effort | Unblocked by |
|---|---|---:|---|
| 1 | [Pricing page with real numbers](#1-pricing-page-with-real-numbers) | 1d | Stripe SKU decisions |
| 2 | [Stripe integration](#2-stripe-integration) | 2-3d | Pricing decisions |
| 3 | [Press kit](#3-press-kit) | 0.5d | None |
| 4 | [Status page](#4-status-page) | 0.5d | Cloud Run alerts wired |
| 5 | [Demo video (~2 min)](#5-demo-video-2-min) | 1d | Pricing copy locked |
| 6 | [Phase 1-5 Zitadel + Permit.io migration](#6-phase-1-5-zitadel--permitio-migration) | ~1w | Soft-launch traffic patterns observed |

## 1. Pricing page with real numbers

A `/pricing` page exists with placeholder content. Public-launch needs
the actual number triple (free / pro / enterprise) wired against
Stripe SKUs. See
[launch-checklist.md L316](./launch-checklist.md) and the broader
monetization context in `.claude/.../memory/project_monetization_strategy.md`.

**Decision needed first:** the per-tier rate-limit caps + Pro/Enterprise
price points. Until those exist as Stripe SKUs, the page can't
faithfully describe what the user gets.

## 2. Stripe integration

Provision a Stripe account, define products (free, pro, enterprise) +
price points, wire customer-portal handoff, write the webhook handler
that bumps `org.tier` + `org.stripe_customer_id` when the subscription
state changes. Architecture is sketched in
[launch-checklist.md L317](./launch-checklist.md).

Org-tier is already in the schema (Phase 6); the gap is the Stripe
half. Hosted Stripe pages take care of the PCI surface; we never
touch card numbers.

## 3. Press kit

A single page (or `/press` route) with:

- Logo files (mark + lockup, light/dark, SVG + PNG @ 400/600/1200)
- One-paragraph description for journalists
- 3-5 hero screenshots
- Founder bios + headshots
- Stats line ("1,000 systems / 1.2M nodes / 321K edges")

Most assets already exist in `frontend/public/logo-*` and
`frontend/public/opengraph-image.tsx`. Collating them into one
authoritative location is the work.

## 4. Status page

Pick one of:

- **statuspage.io** (Atlassian, paid)
- **Better Stack** (free tier covers this)
- **Instatus** (free for one page)
- self-host on Cloudflare Pages with our own component-by-component status JSON

Cloud Run alerts already exist (PR #133). Wire them to the status page
of your choice. ~30 min for setup + ~2 hrs for the integration.

## 5. Demo video (~2 min)

Goal: someone scrolling the landing page should understand the product
in 90 seconds. Suggested script:

- 0-15s - the problem (5 different codes for "truck driver", show the
  matrix)
- 15-45s - browse the website, hit /classify with a real description,
  show the cross-system results
- 45-90s - same query through the API + MCP server (show Claude
  Desktop calling search_classifications)
- 90-120s - call to action (sign up, see /developers)

Tools: Loom for capture, ffmpeg for trim, host on YouTube + embed.

## 6. Phase 1-5 Zitadel + Permit.io migration

Current state: magic-link sign-in via `developers.py`, no central IdP,
no policy engine. Memory references for context:
`.claude/.../memory/project_auth_decision.md` and
`project_authz_decision.md`.

Phases per `auth-implementation.md`:

1. Provision Zitadel Cloud (free tier) at
   `<instance>.zitadel.cloud`
2. Wire Zitadel as the OIDC IdP for the `/login` page (replaces
   magic-link as the only path; magic-link stays as fallback)
3. Migrate `/auth/me` and `/auth/keys` to read Zitadel claims
4. Provision Permit.io (free tier), wire ABAC + ReBAC policy engine
5. Move `require_scope` and `require_tier` checks from in-process to
   Permit.io PDP

Trigger: when magic-link auth proves insufficient at scale, or when
the second product (WoO) needs the same identity layer. Until then,
magic-link + OAuth + slowapi is enough. Don't pre-build identity
infrastructure for traffic that may never arrive.

## How this list should evolve

Cross items off the matrix at the top as they ship. Every item should
move to the launch-checklist's "shipped" log when complete, with a PR
reference. The detailed sections here can then be deleted - the goal
is for this file to shrink to zero entries by public-launch day.
