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
[code]    Merge #119 -> #121 -> #122 -> #124 -> #125
[staging] Run migration + Resend setup on staging (same scripts)
[staging] phase6_smoke.sh AUTOMATED mode against staging
[infra]   Run migration on Cloud SQL prod  (phase6_apply_migration.sh)
[infra]   Provision Resend secret          (phase6_setup_resend.sh)
[deploy]  Cloud Build picks up main, Cloud Run rolls a new revision
[smoke]   Manual walkthrough against prod  (Section 3b)
[smoke]   Optional: phase6_smoke.sh --token <inbox-link> against prod
```

The staging hop is the load-bearing safety net: `DEV_KEYS_DEV_MODE=1`
is fine there, the automated smoke catches contract drift before
anyone touches prod, and prod itself only ever sees a clean human
walkthrough.

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

The smoke script supports two modes. Pick the right one for your
target.

### 3a. Local + staging: AUTOMATED mode

For environments with `DEV_KEYS_DEV_MODE=1` set (signup returns the
magic link in the response body so the script can drive the flow
without an inbox). **Never enable that flag in production** - while
it is on, anyone hitting the signup endpoint with someone else's
email gets a magic link to take over their account.

Staging should run with `DEV_KEYS_DEV_MODE=1` always on; that's
what staging is for.

```bash
# Local
API_BASE=http://localhost:8000 ./scripts/phase6_smoke.sh

# Staging
API_BASE=https://wot-staging.aixcelerator.ai \
EMAIL=smoke+$(date +%s)@colaberry.com \
    ./scripts/phase6_smoke.sh
```

The script walks all six steps (signup, magic-callback, create
key, use key, revoke key, denied on revoked) and prints a green
`Phase 6 smoke: ALL PASS`.

### 3b. Production: MANUAL walkthrough (preferred)

Production is **never** smoked with the automated script. Instead,
do the five-minute click-through:

1. Visit `https://worldoftaxonomy.com/developers/signup` in a
   browser, enter your real email.
2. Wait for the magic-link email (validates Resend wiring end to
   end, not just the code path).
3. Click the link, land on `/developers/keys` with a session
   cookie.
4. Click "Generate key", copy the raw key.
5. From a shell:
   ```bash
   curl -H "Authorization: Bearer <KEY>" \
       https://wot.aixcelerator.ai/api/v1/systems/naics_2022
   # expect 200
   ```
6. Click "Revoke" on the dashboard.
7. Within ~2 seconds:
   ```bash
   curl -i -H "Authorization: Bearer <KEY>" \
       https://wot.aixcelerator.ai/api/v1/systems/naics_2022
   # expect 401 with detail.error == "invalid_api_key"
   ```

This exercises the same six contract assertions the script does,
but uses real Resend delivery + a real human-readable inbox check.
No env-var toggles, no security window.

### 3c. Production: PROD-SAFE script mode (optional)

If you want the script's assertions on prod without the manual
clicking-through-the-UI part, use `--token`:

```bash
# 1. Sign up via the browser (steps 1-2 above) so a real magic-link
#    email arrives in your inbox.
# 2. Copy the value of `t=...` from the link. Run:
API_BASE=https://wot.aixcelerator.ai \
    ./scripts/phase6_smoke.sh --token <PASTE>
```

The script skips the signup step (no `DEV_KEYS_DEV_MODE` needed),
consumes the token, and runs the rest of the assertions. This is
the right choice when you want machine-checked output from prod
without the staging dance.

## 4. Manual sanity checks (optional but recommended)

After the smoke passes, hit a couple of things by hand:

```bash
# 1. Anonymous read still works (30 req/min anonymous bucket).
curl -s https://wot.aixcelerator.ai/api/v1/systems | jq '.[].id' | head -5

# 2. Anonymous on a gated endpoint returns 401 with helpful headers.
curl -i -X POST https://wot.aixcelerator.ai/api/v1/classify \
    -H 'Content-Type: application/json' -d '{"text":"telemedicine"}' \
    | grep -E '^HTTP|^WWW-Authenticate|^Link'

# 3. Visit https://worldoftaxonomy.com/developers/signup in a
#    browser, complete the flow, and check that the magic-link
#    email actually arrives in your inbox (tests Resend wiring,
#    not just NoopEmailClient).
```

## What goes wrong (in order of likelihood)

| Symptom | Likely cause | Fix |
|---|---|---|
| Smoke (automated) step 1 fails: `magic_link_url` missing | `DEV_KEYS_DEV_MODE` not set | Only enable on staging, never on prod. Use `--token` mode against prod instead. |
| Smoke step 2 fails: cookie not set | Cookie is `secure=True` and the test hits HTTP | Run against the HTTPS URL, or set `DEV_SESSION_INSECURE=1` for local only |
| Smoke step 3 fails: 401 on key creation | `dev_session` cookie expired (default 60 min) or `--token` already consumed | Re-run with a fresh signup or a fresh token; magic links are single-use |
| Migration apply fails on `SET NOT NULL` | A row was inserted between backfill and SET NOT NULL during the migration window | Apply during a low-traffic window. The script wraps in `--single-transaction` so a failure rolls back cleanly. |
| Resend script fails: SA missing | Cloud Run service has no pinned SA | Either pin one via `--service-account` or accept the default compute SA the script falls back to. |
| Magic-link email never arrives | `RESEND_API_KEY` not on the active revision | `gcloud run revisions describe $REV --format='value(spec.containers[0].env)'` and re-apply step 2 if missing |
| Prod walkthrough finds magic link in spam | First-send reputation; sender domain not yet warmed | Mark not-spam, then run a few benign sends to the same inbox over the next day; reputation fixes itself. |

## After everything is green

- Flip `docs/handover/launch-checklist.md` Section 3's three
  remaining checkboxes (manual smoke, Cloud SQL migration, Resend
  key).
- Update the GTM thread / launch tracker that the API and MCP
  gates are live.
- Phase 7 (extract dev-key system to `developer.aixcelerator.ai`)
  is the next infra item, but only when WoO is 2-4 weeks from
  launch. No rush.
