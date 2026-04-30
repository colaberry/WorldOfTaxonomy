# Runbooks

Step-by-step responses to alerts that fire against production. Each
runbook follows a fixed shape:

1. **Triage** - what to check first, in what order. The fastest path
   from "page received" to "I know what is broken".
2. **Common causes** - the three or four things this alert usually
   means, ranked by likelihood.
3. **Mitigations** - how to stop bleeding while you investigate.
4. **Root cause** - what to do once the bleeding has stopped.
5. **Followups** - what to fix in code so this alert does not fire
   for the same reason next week.

Always record the request_id (or revision name, or query hash) you
were investigating in the post-incident note. It costs nothing to
write down and saves an hour next time.

## Runbooks in this directory

### Production alerts (page on-call)

- [api-5xx.md](./api-5xx.md) - 5xx error rate is above 1%
- [db-down.md](./db-down.md) - Postgres pool unreachable / `/healthz`
  returning 503
- [auth-broken.md](./auth-broken.md) - 401/403 spike, magic-link
  callbacks failing, dev_session cookie not minting
- [key-validation-slow.md](./key-validation-slow.md) - API-key
  authentication is slow or timing out
- [cloud-run-cold-start-spike.md](./cloud-run-cold-start-spike.md) -
  p95 latency or instance count spiked
- [rate-limit-abuse.md](./rate-limit-abuse.md) - legit users hitting
  429, or a single IP/user saturating capacity

### Operational playbooks (planned actions)

- [deploy-rollback.md](./deploy-rollback.md) - revert a bad backend
  or frontend deploy
- [migrations.md](./migrations.md) - running Alembic migrations in
  dev and production
- [postgres-major-upgrade.md](./postgres-major-upgrade.md) -
  Postgres major-version upgrade (PG 15 -> PG 17) SOP
- [gcp-deploy.md](./gcp-deploy.md) - one-time GCP infra setup for
  Cloud Run + Cloud SQL
- [ingest-failed.md](./ingest-failed.md) - monthly ingest-refresh
  workflow red; stale data warning

### Edge + abuse defense

- [cloudflare-edge.md](./cloudflare-edge.md) - one-time setup of
  Cloudflare in front of Cloud Run for edge DDoS, bot management,
  and a pre-origin rate-limit on signup
- [classify-abuse-defense.md](./classify-abuse-defense.md) - five
  defense layers on the free /classify/demo endpoint (per-IP guard,
  DB-backed budget, Turnstile, disposable-email block, per-email
  cap, MX check) with implementation skeletons for the deferred ones

## Alert sources

The alert thresholds are wired by
[`scripts/phase6_setup_alerts.sh`](../../../scripts/phase6_setup_alerts.sh).
Re-running that script is idempotent and updates the alert text in
place if you change a threshold.

The Sentry inbox is the second source of incidents (uncaught
exceptions). Sentry events do NOT page; they accumulate and are
reviewed during business hours. If a Sentry event is severe enough
to act on immediately, the corresponding 5xx alert will already
have fired.

## On-call rotation

Currently a rotation of one (Ram Katamaraja). Documented in
[cicd-deployment.md](../cicd-deployment.md) under "On-call". Add a
co-on-call before the first paying customer.

## Where to look

| Surface | URL |
|---|---|
| Cloud Logging | `gcloud logging read --project=$PROJECT 'resource.labels.service_name=wot-api' --limit=50` |
| Cloud Run service | `https://console.cloud.google.com/run/detail/us-central1/wot-api/metrics` |
| Cloud SQL | `https://console.cloud.google.com/sql/instances/wot-prod` |
| Sentry inbox | `https://sentry.io/.../wot-api/issues/` |
| Status page | TBD - add when first ten customers are signed up |

## Standard severities

| Severity | When to wake someone | Example |
|---|---|---|
| **Critical** | Page on-call immediately | All 5xx, full outage, security incident |
| **High** | Page during business hours | p95 > 2s but service still serving most requests |
| **Medium** | Slack ping; address within 24h | Single tenant rate-limited unexpectedly |
| **Low** | Tracker ticket; address within a week | Cosmetic 4xx pattern in logs |

The alerts in `phase6_setup_alerts.sh` are configured for **Critical**.
Wire High / Medium / Low manually as needed; this is a launch-baseline,
not the final ops setup.
