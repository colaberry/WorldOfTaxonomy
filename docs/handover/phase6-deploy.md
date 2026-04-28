# Phase 6 deployment handover

This is the runbook for the deploy engineer / operator landing the
four Phase 6 PRs (#119, #121, #122, #124) in production. Three
artifacts:

1. `scripts/phase6_smoke.sh` - end-to-end HTTP smoke (signup ->
   magic-link -> key -> use -> revoke -> denied)
2. `scripts/phase6_apply_migration.sh` - safe Cloud SQL migration
3. `scripts/phase6_setup_resend.sh` - Resend API key in Secret
   Manager + Cloud Run env wiring

## Order of operations

```
[code]   Merge #119 -> #121 -> #122 -> #124 -> #125
[infra]  Run migration on Cloud SQL prod  (phase6_apply_migration.sh)
[infra]  Provision Resend secret          (phase6_setup_resend.sh)
[deploy] Cloud Build picks up main, Cloud Run rolls a new revision
[smoke]  Run phase6_smoke.sh against prod (phase6_smoke.sh)
```

If any step fails, the rollback path is documented inline in each
script's header. The migration is wrapped in a `BEGIN/ROLLBACK`
dry run before commit, so a DDL bug surfaces before touching the
committed schema.

## 1. Apply migration 003 to Cloud SQL

The migration is idempotent (`CREATE TABLE IF NOT EXISTS`,
`ALTER TABLE ... IF NOT EXISTS`, backfill guarded by
`WHERE org_id IS NULL`), wrapped in `--single-transaction`, and
preceded by a `BEGIN; ... ROLLBACK;` dry run.

```bash
# From a workstation with cloud-sql-proxy running, or a Cloud Shell
# with appropriate IAM:
./scripts/phase6_apply_migration.sh \
    --conn 'postgresql://wot_admin@127.0.0.1:5432/worldoftaxanomy' \
    --gcloud-sql-instance wot-prod
```

The script will:

1. Check connectivity + capture pre-counts.
2. Apply the migration inside `BEGIN; ... ROLLBACK;` to surface any
   error before touching the committed schema.
3. Prompt for `apply` to confirm.
4. Run `psql --single-transaction -v ON_ERROR_STOP=1 -f
   migrations/003_phase6_developer_keys.sql`.
5. Print post-state counts plus a per-org breakdown
   (`corporate=N personal=M`) and per-role breakdown
   (`admin=N member=M`) so you can eyeball the backfill.

Rollback path: Cloud SQL automatic backups give point-in-time
recovery via `gcloud sql backups restore --instance=wot-prod`. The
migration is additive so a forward fix is also viable for most bugs.

**Verified clean on `wot-postgres` (local Docker) on 2026-04-28.**

## 2. Provision the Resend secret

Required so `/api/v1/developers/signup` actually sends magic-link
emails (otherwise NoopEmailClient silently drops mail).

```bash
./scripts/phase6_setup_resend.sh \
    --project aixcelerator-prod \
    --service wot-api \
    --region  us-central1
```

The script reads the Resend API key from a TTY prompt (input
hidden, never echoed, not in shell history). Then it:

1. Creates `resend-api-key` in Secret Manager (or adds a new
   version if it already exists).
2. Grants the Cloud Run service account
   `roles/secretmanager.secretAccessor`.
3. Updates the Cloud Run service to expose the secret as
   `RESEND_API_KEY` on every container plus
   `RESEND_SENDER=noreply@aixcelerator.ai` (override via
   `SENDER_EMAIL` env var on the script invocation).
4. Verifies the env var lands on the latest ready revision.

Rotating the key later is a one-liner:

```bash
echo -n "$NEW_KEY" | gcloud secrets versions add resend-api-key \
    --project=aixcelerator-prod --data-file=-
# Cloud Run will pick up the new version on the next revision deploy
# (it's pinned to `:latest`). To force-pull, redeploy with
# `gcloud run services update --tag=...`.
```

## 3. Run the end-to-end smoke

After the four PRs are merged + Cloud Run has rolled a fresh revision
+ Resend is wired up, run the smoke against prod:

```bash
API_BASE=https://wot.aixcelerator.ai \
EMAIL=ram+phase6-smoke@colaberry.com \
    ./scripts/phase6_smoke.sh
```

The script walks all six steps (signup, magic-callback, create key,
use key, revoke key, denied on revoked) and prints a green
`Phase 6 smoke: ALL PASS` if every assertion passes.

**Important:** the API server must be running with
`DEV_KEYS_DEV_MODE=1` for the smoke to work, because the signup
response includes the magic link in the body so the script can drive
the flow without an inbox. **Disable `DEV_KEYS_DEV_MODE` immediately
after the smoke passes** - leaving it enabled in production turns
signup into a passwordless takeover of any email address.

Recommended flow:

```bash
# Temporarily enable DEV mode for the smoke window
gcloud run services update wot-api \
    --project=aixcelerator-prod --region=us-central1 \
    --update-env-vars=DEV_KEYS_DEV_MODE=1

API_BASE=https://wot.aixcelerator.ai ./scripts/phase6_smoke.sh

# Disable immediately after PASS
gcloud run services update wot-api \
    --project=aixcelerator-prod --region=us-central1 \
    --remove-env-vars=DEV_KEYS_DEV_MODE
```

If you'd rather run the smoke against a staging deployment, point
`API_BASE` at staging and skip the prod env-var dance entirely.

## 4. Manual sanity checks (optional but recommended)

After the smoke passes, hit a couple of things by hand:

```bash
# 1. Anonymous read still works (30 req/min anonymous bucket).
curl -s https://wot.aixcelerator.ai/api/v1/systems | jq '.[].id' | head -5

# 2. Anonymous on a gated endpoint returns 401 with helpful headers.
curl -i https://wot.aixcelerator.ai/api/v1/export/systems.jsonl \
    | grep -E '^HTTP|^WWW-Authenticate|^Link'

# 3. Visit https://worldoftaxonomy.com/developers/signup in a
#    browser, complete the flow, and check that the magic-link
#    email actually arrives in your inbox (tests Resend wiring,
#    not just NoopEmailClient).
```

## What goes wrong (in order of likelihood)

| Symptom | Likely cause | Fix |
|---|---|---|
| Smoke step 1 fails: `magic_link_url` missing | `DEV_KEYS_DEV_MODE` not set on the server | `gcloud run services update --update-env-vars=DEV_KEYS_DEV_MODE=1` |
| Smoke step 2 fails: cookie not set | Cookie is `secure=True` and the test hits HTTP | Run against the HTTPS URL, or set `DEV_SESSION_INSECURE=1` for local |
| Smoke step 3 fails: 401 on key creation | `dev_session` cookie expired (default 60 min) | Re-run the smoke; curl creates a fresh cookie each time |
| Migration apply fails on `SET NOT NULL` | A row was inserted between backfill and SET NOT NULL during the migration window | Apply during a low-traffic window. The script wraps in `--single-transaction` so a failure rolls back cleanly. |
| Resend script fails: SA missing | Cloud Run service has no pinned SA | Either pin one via `--service-account` or accept the default compute SA the script falls back to. |
| Magic-link email never arrives | `RESEND_API_KEY` not on the active revision | `gcloud run revisions describe $REV --format='value(spec.containers[0].env)'` and re-apply step 2 if missing |

## After everything is green

- Flip `docs/handover/launch-checklist.md` Section 3's three
  remaining checkboxes (manual smoke, Cloud SQL migration, Resend
  key).
- Update the GTM thread / launch tracker that the API and MCP
  gates are live.
- Phase 7 (extract dev-key system to `developer.aixcelerator.ai`)
  is the next infra item, but only when WoO is 2-4 weeks from
  launch. No rush.
