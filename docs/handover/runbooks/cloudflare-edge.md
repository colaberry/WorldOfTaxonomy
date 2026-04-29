# Runbook: Cloudflare in front of Cloud Run

**Goal:** put Cloudflare's edge between the public internet and the
Cloud Run service so that L7 DDoS, basic bot management, and WAF
rules are enforced before any request reaches our origin. Works on
the Cloudflare free tier; takes about an hour to wire up the first
time.

**Why:** the in-process and DB-backed rate-guards in
`world_of_taxonomy.api.rate_guard` cap per-IP and global signup
volume, but they only run AFTER Cloud Run has accepted the
connection. A meaningful fraction of bot traffic never gets that
far when Cloudflare is in front: scrapers, simple botnets, and
amateur DDoS are dropped at the edge for free.

This is one of the four bot-defense layers
([`docs/handover/launch-checklist.md`](../launch-checklist.md)
calls them out as A/B/C/E). A and B already shipped in code; this
runbook is C. E is a single Cloud Run flag.

## Prerequisites

- Domain `worldoftaxonomy.com` already on Cloudflare DNS (it is).
- Cloud Run service deployed at the current direct URL
  (`wot.aixcelerator.ai`).
- gcloud + Cloudflare dashboard access.

## Step 1: Cloudflare custom hostname

1. Cloudflare dashboard -> Workers & Pages -> Domains -> Add
   custom hostname `wot.aixcelerator.ai` (or whichever domain we
   want the edge to terminate on).
2. Cloudflare auto-issues an edge cert; wait for "Active".
3. Add a CNAME record `wot.aixcelerator.ai -> wot-cloudrun.<...>.run.app`
   (the bare Cloud Run hostname). Mark proxied (orange cloud).

## Step 2: Cloud Run domain mapping

```bash
gcloud beta run domain-mappings create \
    --service wot-api \
    --domain wot.aixcelerator.ai \
    --region us-central1 \
    --project aixcelerator-prod
```

Cloud Run waits for ACME validation. Cloudflare proxied DNS handles
the redirection; expected ~1-2 minutes.

## Step 3: Cloudflare WAF + bot management

Settings -> Security -> Bot Fight Mode: ON (free tier). This drops
verifiably-known bots (scrapers, headless Chromium without a real
TLS fingerprint) before they hit the origin.

Add three custom rules under Security -> WAF:

1. **Block known abusers** by ASN.
   ```
   (cf.threat_score gt 14)
   ```
   Action: Managed Challenge.

2. **Rate-limit signup endpoint at the edge.**
   ```
   (http.request.uri.path eq "/api/v1/developers/signup")
   ```
   Action: Rate Limit -> 5 requests / 10 minutes / IP. Mirrors the
   in-process per-IP cap but enforced at edge so the request never
   reaches Cloud Run.

3. **Block obviously-bad user agents** (curl in headers without a
   token, empty UA, `python-requests/2.x`).
   ```
   (http.user_agent eq "" or http.user_agent contains "python-requests")
       and not (http.request.headers.x-wot-internal eq "<value>")
   ```
   Action: Block. Carve-out for our own internal probes via
   `X-WoT-Internal: <secret>` header so scripted health checks
   aren't blocked.

## Step 4: Cloudflare Page Rules (caching for read endpoints)

`/api/v1/systems`, `/api/v1/systems/{id}`, and `/api/v1/healthz`
are safe to cache at the edge for short TTLs. Saves Cloud Run
cycles + accelerates anonymous browsing.

- Page Rule 1: `wot.aixcelerator.ai/api/v1/systems*` -> Cache
  Level: Cache Everything; Edge Cache TTL: 5 minutes.
- Page Rule 2: `wot.aixcelerator.ai/api/v1/healthz` -> Cache
  Level: Bypass (we want fresh every time).

Authenticated endpoints (`Authorization` header present) are
NOT cached because Cloudflare's "Cache Everything" still respects
`Cache-Control: private` from the origin.

## Step 5: Verify

```bash
# CF should now sit in front. Headers from edge:
curl -sI https://wot.aixcelerator.ai/api/v1/healthz \
    | grep -iE "cf-ray|cf-cache-status|server"
# Expect:
#   cf-ray: <hex>-<airport>
#   cf-cache-status: BYPASS  (per page rule 2)
#   server: cloudflare

# Verify rate-limit edge rule:
for i in 1 2 3 4 5 6 7 8; do
    curl -s -o /dev/null -w "%{http_code} " \
         -X POST https://wot.aixcelerator.ai/api/v1/developers/signup \
         -H 'Content-Type: application/json' \
         -d '{"email":"smoke@gmail.com"}'
done
# Expect 202s for the first 5, then 429 from Cloudflare (not Cloud Run).
```

The 429 from Cloudflare can be distinguished by:

- `cf-ray` header present
- `server: cloudflare`
- response body is HTML (Cloudflare's own page), not our JSON

When Cloud Run returns 429 (in-process rate guard), the body is JSON
with `detail.error == "rate_limit_exceeded"` and `cf-cache-status:
DYNAMIC`. Both are valid; the edge rule fires first when triggered.

## Step 6: Make the in-process rate guard log the real client IP

Cloudflare adds `CF-Connecting-IP` and updates `X-Forwarded-For` so
the origin sees Cloudflare proxy IPs in `request.client.host`.
`world_of_taxonomy.api.rate_guard._client_ip` already reads
`X-Forwarded-For` first, so it gets the real client. Verify by
hitting any endpoint and grepping the access log:

```bash
gcloud logging read \
    --project=aixcelerator-prod \
    "resource.labels.service_name=wot-api" \
    --limit=1 --order=desc \
    --format='value(jsonPayload.ip)'
```

If the value is a Cloudflare proxy IP (one of
[their published ranges](https://www.cloudflare.com/ips/)), the
header chain is broken. Diagnose with `request.headers` in a
test endpoint; usually the fix is to also honor `CF-Connecting-IP`
ahead of `X-Forwarded-For` in `_client_ip`.

## Cost

- Cloudflare free tier covers everything in steps 1-3 + page rules.
- Bot Fight Mode + standard WAF rules: free.
- Custom hostname + edge cert: free.
- Pro plan ($20/month per domain) adds image optimization, more
  page rules, faster purge. Defer until traffic actually warrants.

## Rollback

If Cloudflare causes issues:

1. Cloudflare dashboard -> DNS -> change orange cloud to grey on
   the CNAME for `wot.aixcelerator.ai`. Traffic now goes
   direct-to-Cloud-Run; no proxy in path.
2. Diagnose Cloudflare-side issue.
3. Re-enable proxy with grey-to-orange flip.

DNS propagation is ~30 seconds via Cloudflare; rollback is fast.

## What this runbook does NOT do

- **Cloudflare Turnstile** (CAPTCHA on the signup form). Separate
  setup, ~2 hours frontend work, only worth doing if the rate
  guards prove insufficient. The Turnstile token would be checked
  on the backend in the signup handler, gated by env var.
- **Cloudflare R2 / Pages** for the frontend. We're on
  Vercel + Cloud Run today. Switching CDNs is its own decision.
- **Cloudflare Tunnel** to make Cloud Run private (no public URL).
  Possible but adds operational complexity for marginal benefit at
  our scale.

## Related

- [`api-5xx.md`](./api-5xx.md) - what to do when Cloud Run is 5xxing
  (Cloudflare layer caches some of the noise).
- `world_of_taxonomy/api/rate_guard.py` - the in-process and
  DB-backed guards Cloudflare is augmenting.
