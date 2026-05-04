# Runbook: Rate limit abuse

## Symptom

- Spike in 429 responses in access logs.
- Legit users reporting "API suddenly returning rate limit errors."
- One IP or one authenticated user accounts for >50% of traffic.

## Impact

- **Legit anonymous traffic** throttled at 30 req/min per IP.
- **Paid users** should not normally see 429s unless they exceed tier caps (1000/min pro, 10000/min enterprise; daily caps in `TIER_DAILY_LIMITS`).
- **Cost**: sustained abuse on anonymous tier inflates backend compute (Fly machine time) and database compute (usage-billed providers like Neon, Supabase) or connection/IO on self-hosted.

## Detection

```bash
# Top IPs by request count in the last hour (JSON access log)
fly logs -a wot-api | jq -r 'select(.status) | .ip' | sort | uniq -c | sort -rn | head -20

# 429 rate over the last hour
fly logs -a wot-api | jq 'select(.status == 429) | .ip' | sort -u | wc -l

# Top users by request count
fly logs -a wot-api | jq -r 'select(.user_id) | .user_id' | sort | uniq -c | sort -rn | head -20
```

## Diagnosis

| Pattern | Likely cause |
|---------|--------------|
| One IP, one path, steady rps | Scraper or misconfigured cron |
| One IP, full route sweep | Unpaid bulk extraction |
| Many IPs, same user-agent | Botnet or scraping as a service |
| Authenticated user burning through daily cap | Legitimate usage outgrew tier |
| Sudden global 429 spike with no single heavy caller | Rate limit config regression; check `TIER_RATE_LIMITS` in `world_of_taxonomy/api/middleware.py` |

## Mitigation

1. **Legit user** who outgrew their tier: email + offer an upgrade or a temporary tier bump:
   ```sql
   UPDATE app_user SET tier = 'pro' WHERE id = <user_id>;
   ```
   (Be explicit: this is a manual override until billing lands.)
2. **Abuser**: block at the Fly edge or via Cloudflare (when fronted). Short-term, add to a blocklist env var and plumb through the rate-limit middleware if the pattern persists.
3. **Rate-limit misconfig**: revert the middleware change or redeploy last-known-good.

## Remediation

- Consider **tightening anon daily cap** (`TIER_DAILY_LIMITS["anonymous"]`, currently 1000/day) if scraping is persistent.
- Consider **per-route weights** so expensive endpoints (bulk export, classify) cost more than `GET /systems`.
- Add a documented **contact for commercial bulk access** on the rate-limit 429 message so heavy users self-convert.

## Postmortem checklist

- Duration and request volume of the abuse window.
- Infra cost delta for the day (backend host + database).
- Whether any customer-facing 429s fell on paying users.
- Follow-ups: do we need Cloudflare in front? Should MCP have its own rate-limit scope?
