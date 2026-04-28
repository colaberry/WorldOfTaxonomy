# API Keys - Get One, Use One, Rotate One

WorldOfTaxonomy gates the public API and MCP server with developer
keys. This page is the short version: get a key, use it, rotate it
when you need to.

## Getting a key (60 seconds)

1. Go to [worldoftaxonomy.com/developers/signup](https://worldoftaxonomy.com/developers/signup).
2. Enter your email. We send a one-time sign-in link (no password,
   ever - same pattern as Vercel, Linear, and Notion).
3. Click the link in your inbox. You land on `/developers/keys`
   with a session cookie set.
4. Click "Generate key", give it a name (e.g. "MCP on laptop",
   "CI runner"), pick a scope.
5. Copy the raw key. It is shown once and never again. Store it in
   your password manager or secret store immediately.

## Using a key

Pass it as a Bearer token on every request:

```bash
curl -H "Authorization: Bearer wot_a3f2c5d9...x4z1" \
    https://wot.aixcelerator.ai/api/v1/systems/naics_2022
```

Or for the MCP server, set it as an environment variable:

```bash
WOT_API_KEY=wot_a3f2c5d9...x4z1 uvx worldoftaxonomy-mcp
```

## Key prefixes (what they mean)

The prefix encodes the scope at issuance time, mirroring Stripe and
GitHub conventions. Knowing the prefix is enough to triage a leaked
key without looking it up.

| Prefix | Meaning |
|---|---|
| `wot_xxx...` | Full-access single-product (WoT) key |
| `rwot_xxx...` | Restricted (subset of WoT actions, e.g. read-only) |
| `aix_xxx...` | Cross-product key spanning the aixcelerator.ai portfolio |
| `woo_`, `wouc_`, `woa_` | Same shape on sibling products when they ship |

## Scopes

Scopes follow a `<product>:<action>` grammar. Available WoT scopes:

| Scope | Allows |
|---|---|
| `wot:read` | Reading systems, nodes, equivalences |
| `wot:list` | Listing endpoints (search, browse) |
| `wot:export` | Bulk JSONL exports (Pro+) |
| `wot:classify` | Classify free-text against taxonomies (Pro+) |
| `wot:admin` | Admin-only endpoints (taxonomy generation) |
| `wot:*` | All of the above |

Pick the narrowest scope that does the job. A key with `wot:read`
that gets pasted in a public repo only exposes read traffic; a
`wot:*` key in the same place is a bigger blast radius.

## Rate limits

Limits are enforced **at the org level**, not per user. Every signup
is bucketed into an org from day 1:

- Email at a company domain (e.g. `you@acme.com`) joins the shared
  `acme.com` org. All employees share one rate-limit pool.
- Email at a personal-domain provider (gmail, yahoo, hotmail,
  outlook, proton, icloud, fastmail) gets a per-email personal org.

| Tier | Pool (per minute) |
|---|---|
| Anonymous (no key) | 30 |
| Free (your org) | 1,000 shared |
| Pro | 10,000 shared |
| Enterprise | configurable |

If your team is hitting 429s, the fix is either upgrading the org
tier or splitting load across more time. Per-user keys do not
multiply the pool.

## Revoking and rotating

A revoked key returns 401 within ~2 seconds across the whole fleet.
Workflows:

- **Compromise:** revoke the key on `/developers/keys`, generate a
  fresh one, deploy. The old key is dead.
- **Rotation:** generate the new key first, deploy it everywhere,
  then revoke the old one. No downtime.
- **Expiry:** when creating a key, optionally set `expires_in_days`.
  Useful for short-lived CI tokens.

## Errors you may hit

| Status | Body | Meaning |
|---|---|---|
| 401 `missing_api_key` | "API key required..." | No `Authorization: Bearer` header |
| 401 `invalid_api_key` | reason: `not_found` / `revoked` / `expired` | Key did not validate |
| 403 `scope_missing` | required_scope: `wot:export` | Key has no scope for this endpoint |
| 403 `tier_required` | required_tier: `pro or enterprise` | Endpoint needs a higher org plan |
| 429 (rate limit) | retry_after | Org pool exhausted |

Each error response carries a `Link: <...>; rel="signup|manage|upgrade"`
header pointing at the page that fixes it.

## Self-hosting

The full project is MIT-licensed. If you'd rather run your own
instance:

```bash
git clone https://github.com/colaberry/WorldOfTaxonomy
cd WorldOfTaxonomy
# Set DATABASE_URL, JWT_SECRET, then:
python3 -m uvicorn world_of_taxonomy.api.app:create_app --factory
```

In a self-hosted setup you can choose to disable auth entirely
(`DISABLE_AUTH=1`), keep the developer-key system, or layer on your
own gateway.

## What goes wrong

- **Magic-link email never arrives.** Check spam first. If the page
  said "we sent a sign-in link" but nothing comes through, our
  Resend configuration may be off; report at
  [github.com/colaberry/WorldOfTaxonomy/issues](https://github.com/colaberry/WorldOfTaxonomy/issues).
- **`scope_missing` on an endpoint you used to be able to call.**
  You probably issued a restricted key. Generate a new one with the
  scope the endpoint requires, or use `wot:*` if you want one key
  for everything.
- **`tier_required` with a valid scope.** That endpoint needs a
  paid plan. See [/pricing](https://worldoftaxonomy.com/pricing).
- **429 inside a single browser tab.** Someone else at your org
  domain is using the API. Look at the org dashboard (Phase 8) when
  it ships, or upgrade the org tier.

## Related

- [Getting Started](/guide/getting-started) - end-to-end first
  request walkthrough
- [MCP Setup](/guide/mcp-setup) - per-client config snippets for
  Claude Desktop, Cursor, Zed, and more
- [/developers](/developers) - SDK examples and skill-bundle
  installation
- [/developers/keys](/developers/keys) - manage your keys
