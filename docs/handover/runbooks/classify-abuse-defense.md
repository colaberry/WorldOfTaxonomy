# Runbook: /classify abuse-defense layers

The free `/classify/demo` endpoint is the highest-value abuse target on
the site: every call is LLM-backed (real cost) and every accepted
request writes a row to `classify_lead` (downstream lead-pipeline
noise). This runbook lists the five defense layers - which are
shipped, which are deferred, and the implementation skeleton for each
deferred layer so a future operator can flip them on without
re-deriving the design.

## Status snapshot

| # | Layer | Status |
|---|---|---|
| A | Cloudflare Turnstile on the form | DEFERRED - wire when Cloudflare goes in front of Cloud Run |
| **B** | **DB-backed `classify_lead` budget per hour** | **SHIPPED** (this PR) |
| - | Per-IP rate guard (20/hour) | SHIPPED in PR #144 |
| - | slowapi anon (30/min) | SHIPPED pre-Phase-6 |
| - | Frontend regex format check | SHIPPED |
| C | Disposable-email blocklist | DEFERRED - low/medium value, ~30 min |
| D | Per-email cap | DEFERRED - regressive against power users, ~30 min |
| E | MX deliverability check | DEFERRED - adds latency, ~30 min |

## When to wire each deferred layer

Trigger the additional layers only if real abuse signal appears.
Specifically:

- **A (Turnstile)**: when Cloudflare wiring lands (item 4 of the
  soft-launch operator action list). Free, single-toggle once Cloudflare
  is in front; no reason to skip.
- **C (disposable blocklist)**: when more than ~5% of `classify_lead`
  rows have `@mailinator.com`-style domains AND we're trying to use
  the leads for marketing.
- **D (per-email cap)**: when a single email value appears more than
  ~50 times in `classify_lead` in 24 hours (someone has fixed on a
  fake email and is farming).
- **E (MX check)**: only if the lead-list quality matters for
  enterprise outreach AND C alone doesn't get domain-quality high
  enough.

The 503 from layer B already protects against runaway cost; the rest
of these are about lead-list cleanliness, not cost protection.

## Implementation skeletons

### A. Cloudflare Turnstile

Backend (`world_of_taxonomy/api/routers/classify_demo.py`):

```python
import os
import httpx

_TURNSTILE_SECRET_ENV = "CLOUDFLARE_TURNSTILE_SECRET"
_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def _verify_turnstile(token: str, remote_ip: str | None) -> bool:
    secret = os.environ.get(_TURNSTILE_SECRET_ENV, "").strip()
    if not secret:
        # Not configured: pass through (dev / pre-prod).
        return True
    async with httpx.AsyncClient(timeout=4.0) as http:
        r = await http.post(
            _TURNSTILE_VERIFY_URL,
            data={"secret": secret, "response": token, "remoteip": remote_ip or ""},
        )
        r.raise_for_status()
        return r.json().get("success") is True


# In the route handler, after the rate guards but before the LLM call:
class ClassifyDemoRequest(BaseModel):
    email: str
    text: str
    countries: Optional[list[str]] = None
    turnstile_token: Optional[str] = None  # added field

# ...
if not await _verify_turnstile(body.turnstile_token, _client_ip(request)):
    raise HTTPException(
        status_code=403,
        detail={"error": "turnstile_failed", "message": "Anti-bot challenge failed."},
    )
```

Frontend (`frontend/src/app/classify/ClassifyTool.tsx`):

```tsx
import Script from 'next/script'

// In the form:
<Script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer />
<div
  className="cf-turnstile"
  data-sitekey={process.env.NEXT_PUBLIC_CLOUDFLARE_TURNSTILE_SITEKEY}
  data-callback="onTurnstileVerify"
/>

// Read window.turnstileToken from the data-callback handler before submit.
```

Env vars to provision:
- `CLOUDFLARE_TURNSTILE_SECRET` (Cloud Run secret)
- `NEXT_PUBLIC_CLOUDFLARE_TURNSTILE_SITEKEY` (public, baked into the build)

Provider setup: Cloudflare dashboard -> Turnstile -> Add Site -> select
"Invisible" challenge for soft launch (less friction). See
[`cloudflare-edge.md`](./cloudflare-edge.md) for the full Cloudflare-edge
context.

### C. Disposable-email blocklist

A static list of ~200-500 disposable-email domains is enough to catch
the volume of garbage. Source candidates:

- [disposable-email-domains/disposable-email-domains](https://github.com/disposable-email-domains/disposable-email-domains)
  (~3000-domain JSON list, MIT, weekly-updated)
- Tighter curated list: top 200 from the above by volume

Backend addition to `classify_demo.py`:

```python
# Load once at module import.
_DISPOSABLE_DOMAINS: frozenset[str] = frozenset(
    line.strip().lower()
    for line in (Path(__file__).parent / "disposable_domains.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
)


def _email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].strip().lower()


# In ClassifyDemoRequest's email validator (or a separate gate above
# the rate-guard call):
if _email_domain(body.email) in _DISPOSABLE_DOMAINS:
    raise HTTPException(
        status_code=400,
        detail={
            "error": "disposable_email",
            "message": (
                "Please use a non-temporary email. We send occasional "
                "product updates that disposable inboxes will miss."
            ),
        },
    )
```

Refresh procedure: pull the JSON list, regenerate `disposable_domains.txt`,
commit. ~1 minute monthly.

Trade-off: legitimate users sometimes use disposable emails for one-off
explorations. We block them, slightly hurting conversion. Worth it only
if lead-list quality is a real bottleneck.

### D. Per-email cap (e.g., max 5/day per email)

Backend addition (`rate_guard.py`):

```python
async def check_per_email_classify_cap(
    conn,
    email: str,
    *,
    max_per_day: int = 5,
) -> None:
    """Refuse with 429 when the same email value has submitted more
    than `max_per_day` classify queries in the last 24 hours.

    Intended to catch the 'attacker memorizes one fake email and farms
    it' pattern. Unhelpful against rotating-email attackers (those are
    caught by the per-IP guard + the global classify_lead budget).

    Hashes the email so the lookup matches our bcrypt-hash storage in
    classify_lead.email_hash (proposed schema change; today the column
    stores plaintext - see migration 005 sketch below).
    """
    if max_per_day <= 0:
        return
    count = await conn.fetchval(
        """SELECT count(*)
           FROM classify_lead
           WHERE email = $1
             AND created_at > NOW() - INTERVAL '1 day'""",
        email.strip().lower(),
    )
    if count is not None and count >= max_per_day:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "per_email_cap_exceeded",
                "scope": "classify_lead_per_email",
                "retry_after_seconds": 24 * 3600,
            },
            headers={"Retry-After": str(24 * 3600)},
        )
```

Wire it in `/classify/demo` after `check_classify_lead_budget`.

Trade-off: power users sometimes legitimately try ~10-20 prompts in a
session refining their description. They would hit this cap. A
softer alternative: throttle response time progressively rather than
hard-deny. But that's more code than it's worth for soft launch.

### E. MX deliverability check

```python
import asyncio
import socket
import dns.resolver  # add `dnspython` to requirements.txt

_MX_RESOLVER = dns.resolver.Resolver()
_MX_RESOLVER.lifetime = 2.0  # seconds, hard cap


async def _has_mx(domain: str) -> bool:
    """True if the domain has at least one MX record. False on NXDOMAIN
    or no-records. Cached for 1 hour at module level (in-memory)."""
    loop = asyncio.get_event_loop()
    try:
        answers = await loop.run_in_executor(
            None, lambda: _MX_RESOLVER.resolve(domain, "MX")
        )
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False
    except Exception:
        # Resolver timeout or transient error: fail open (don't block
        # legitimate users on a flaky DNS).
        return True
```

Add a small in-memory LRU cache on `_has_mx` so we don't DNS-query
gmail.com on every classify. ~50 lines.

Trade-off: adds ~100-300ms of latency on first-seen domains (cached
after). Failure mode: fail open on resolver timeouts means an attacker
who can DDoS our DNS resolver gets through. Acceptable.

## Operational notes

### Tuning the layer-B cap

The default `CLASSIFY_LEAD_BUDGET_PER_HOUR=500` should comfortably
fit even a launch-day spike. To raise during a real spike (HN front
page, Product Hunt traction):

```bash
# Cloud Run console -> Edit & Deploy New Revision -> Variables & Secrets
# Set CLASSIFY_LEAD_BUDGET_PER_HOUR=2000 -> Deploy.
# Takes ~30s, no downtime.
```

Watching the cap: `wot_rate_guard_fired_total{endpoint="classify_lead_budget"}`
counter. If it climbs > 0 in normal traffic, the cap is too low. If it
stays at 0 during a spike, the cap is high enough.

### When the cap fires legitimately

503 responses from `/classify/demo` will be served until the rolling
hour clears. Frontend should display a friendly banner; the response
body has `detail.error == "classify_budget_exhausted"` for client-side
detection.

If a legitimate spike trips the cap mid-launch, raise the env var
(no code change needed) and let the next hour clear.

## Why these were not all shipped

Speed-to-launch trade-off. Layer B alone takes us from "distributed
attacks unbounded" to "hard ceiling at 500/hour." A is the next-best
single layer but requires Cloudflare to be wired first. C/D/E are
lower-leverage and can land lazily based on observed abuse.
