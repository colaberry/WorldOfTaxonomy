# Runbook: Auth broken

## Symptom

- Spike in 401/403 responses on `/api/v1/*` routes.
- Users report "I can't log in" or "my API key stopped working."
- OAuth callbacks land on `/auth/callback` with an error query param (`?error=oauth_exchange_failed` or similar).

## Impact

- **Logged-in users** may get bounced to login even with a valid session.
- **API clients** using `Authorization: Bearer wot_...` keys get 401.
- **Rate limiting** falls back to IP-based anonymous limits (30/min), so heavy users throttle.
- `/api/v1/healthz` still returns 200 because it does not exercise auth.

## Detection

```bash
# Grep Fly logs for auth errors in the last 15 minutes
fly logs -a wot-api | grep -E 'JWTError|InvalidTokenError|401|403' | tail -50

# Hit a protected route with a known-good key
curl -H "Authorization: Bearer $WOT_TEST_KEY" \
     https://wot.aixcelerator.ai/api/v1/auth/me
```

## Diagnosis

| Check | Command / URL | Tells you |
|-------|---------------|-----------|
| JWT_SECRET rotated without redeploy | `fly secrets list -a wot-api` | Mismatched secret vs signed tokens in the wild |
| Clock drift | Compare `date -u` on the box vs NTP | JWT `exp` claims rejected as expired |
| bcrypt module load failure | Start-up logs | Password login broken, API keys unaffected |
| OAuth provider outage | GitHub / Google / LinkedIn status pages | Callbacks failing at the exchange step |
| Database down | See `db-down.md` | `app_user` and `api_key` tables unreachable |
| `DISABLE_AUTH=true` leaked to prod | `fly ssh console -C 'env' -a wot-api | grep DISABLE_AUTH` | All requests get synthetic "dev" user |

## Mitigation

1. **If JWT_SECRET is suspected rotated**, do NOT rotate again under pressure -- that invalidates every session. First confirm the current value matches what signed the in-flight tokens.
2. **If OAuth is broken but password+API key login still works**, disable the offending provider by unsetting its client id:
   ```bash
   fly secrets unset GITHUB_CLIENT_ID -a wot-api
   ```
   The frontend OAuth button hides when the authorize endpoint returns 400.
3. **Post a notice** pointing API users at key-based auth if password login is the broken surface.

## Remediation

- **JWT_SECRET too short (<32 chars)**: `_validate_env()` in `world_of_taxonomy/api/app.py` rejects this at startup. If it still happened, the env var was set after the fact; redeploy.
- **Token exp too aggressive**: default is 15 minutes (see `world_of_taxonomy/api/routers/auth.py`). Bump with care -- longer-lived tokens are harder to revoke.
- **OAuth redirect URI mismatch after domain change**: update the redirect URIs at the provider (GitHub / Google / LinkedIn) to match `FRONTEND_URL/auth/callback`. See `OAUTH_PRODUCTION_SETUP.md`.
- **API key prefix index corrupted**: very rare; confirm `api_key.prefix` column is populated and the partial index exists.

## Postmortem checklist

- Which auth flow broke (password, JWT validation, API key, OAuth)?
- Duration and error count.
- Whether `DISABLE_AUTH` was involved (it should never be true in prod).
- Whether rate-limit fallout cascaded (users throttled on anon tier).
- Follow-ups: should the OAuth callback surface a friendlier error? Should we alert on 401 rate rather than just error rate?
