# Runbook: Auth broken

## Symptom

- Spike in 401/403 responses on `/api/v1/*` routes.
- Users report "I can't sign in" or "my magic-link is being rejected."
- API clients using `Authorization: Bearer wot_...` keys get 401.
- Magic-link callback at `/auth/magic` lands users on the error state ("Sign-in link is invalid").

## Impact

- **New sign-ups** can't complete - the email arrives but the link 401s.
- **Existing dashboard users** get bounced to `/login` even with a valid `dev_session` cookie if JWT signing is broken.
- **API clients** using `wot_/rwot_/aix_` keys get 401 on the API.
- **Rate limiting** falls back to IP-based anonymous limits (30/min), so heavy users throttle.
- `/api/v1/healthz` still returns 200 because it does not exercise auth.

## Detection

```bash
# Cloud Run logs for auth errors in the last 15 minutes
gcloud logging read \
    --project=$PROJECT \
    "resource.labels.service_name=wot-api AND \
     (textPayload:JWTError OR textPayload:InvalidTokenError OR \
      textPayload:401 OR textPayload:403)" \
    --limit=50 --freshness=15m

# Hit a protected route with a known-good API key
curl -H "Authorization: Bearer $WOT_TEST_KEY" \
     https://wot.aixcelerator.ai/api/v1/systems/naics_2022

# Hit the magic-link signup with a test email; should 202
curl -X POST https://wot.aixcelerator.ai/api/v1/developers/signup \
    -H 'Content-Type: application/json' \
    -d '{"email":"test+'"$(date +%s)"'@gmail.com"}'
```

## Diagnosis

| Check | Command / URL | Tells you |
|-------|---------------|-----------|
| `JWT_SECRET` rotated without redeploy | `gcloud run services describe wot-api --format='value(spec.template.spec.containers[0].env)'` | Mismatched secret vs signed `dev_session` cookies in the wild - every signed-in user is logged out |
| Clock drift | Compare `date -u` on the container vs NTP | `exp` claims rejected as expired |
| bcrypt module load failure | Cloud Run start-up logs | API-key validation broken (bcrypt-checks the hash on every request) |
| Resend API key invalid / quota exceeded | Resend dashboard, `RESEND_API_KEY` env value | Magic-link emails not delivered. Backend silently falls through to NoopEmailClient and the user never receives the link. |
| Email-send budget exhausted | `wot_rate_guard_fired_total{endpoint="email_send_budget"}` counter | 503 on `/developers/signup` until the rolling hour clears. Bump `EMAIL_SEND_BUDGET_PER_HOUR` env var if legitimate. |
| `email_send_log` table missing or unreachable | DB query | Same 503 - the budget query fails open or fails closed depending on the helper |
| Database down | See [`db-down.md`](db-down.md) | `app_user`, `api_key`, `magic_link_token`, `email_send_log`, `classify_lead` tables unreachable |
| `DISABLE_AUTH=true` leaked to prod | `gcloud run services describe wot-api --format='value(spec.template.spec.containers[0].env)' \| grep DISABLE_AUTH` | All requests get synthetic "dev" user |

## Mitigation

1. **If `JWT_SECRET` is suspected rotated**, do NOT rotate again under pressure - that invalidates every session. First confirm the current value matches what signed the in-flight cookies. Sessions issued before the rotation are dead either way; users must re-sign-in via magic link.
2. **If Resend is broken**, sign-up via magic-link is dead until it's restored. The `/developers/keys` dashboard remains accessible to users with an unexpired `dev_session` cookie. Existing API-key holders are unaffected (no email path on that flow). Post a notice on the status page if customers are blocked at sign-up.
3. **If the email-send budget is tripping repeatedly**, raise `EMAIL_SEND_BUDGET_PER_HOUR` (env var, no code change). Watch the `wot_rate_guard_fired_total{endpoint="email_send_budget"}` counter to confirm it stops climbing.

## Remediation

- **`JWT_SECRET` too short (<32 chars)**: `_validate_env()` in `world_of_taxonomy/api/app.py` rejects this at startup. If it still happened, the env var was set post-deploy; redeploy.
- **`dev_session` cookie TTL too aggressive**: default is 60 minutes (env var `DEV_SESSION_TTL_MINUTES` in `developers.py`). Bump with care - longer-lived sessions are harder to revoke since `/api/v1/auth/logout` only clears the cookies on the user's browser, not server-side state.
- **API-key prefix index corrupted**: very rare; confirm `api_key.key_prefix` column is populated and `idx_api_key_key_prefix` exists. Re-create with `REINDEX INDEX idx_api_key_key_prefix;` if needed.
- **Magic-link tokens not single-use**: a sign of `magic_link_token.consumed_at` not being set in the callback. Read `developers.py auth_magic_callback`. Tokens are invalidated by `UPDATE ... RETURNING` semantics; if that pattern is broken, every link works multiple times. Critical, file an incident.

## Postmortem checklist

- Which auth surface broke (magic-link sign-up / sign-in, `dev_session` cookie validation, API-key validation, sign-out)?
- Duration and error count.
- Whether `DISABLE_AUTH=true` was involved (it should never be `true` in prod).
- Whether rate-limit fallout cascaded (users throttled on anon tier).
- Whether the email-send budget was the trigger or just a downstream symptom.
- Follow-ups: should the magic-link callback surface a friendlier error? Should we alert on 401 rate rather than just error rate? Is `EMAIL_SEND_BUDGET_PER_HOUR` tuned correctly for the launch traffic profile?
