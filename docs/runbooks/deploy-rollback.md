# Runbook: Deploy rollback

## Symptom

- Error rate or latency spike that correlates with a deploy timestamp.
- A specific feature broke and the fix is not obvious within 5 minutes.
- Sentry issue count jumps right after a release.

## Impact

- User-facing regressions until rollback completes.
- Rolling forward a broken fix often takes longer than reverting.

## Decision rule

If the incident is **user-visible** and **started within 10 minutes of a deploy**, roll back first, diagnose second. Rolling forward is for bugs discovered during business hours with time to fix properly.

## Backend rollback (Fly)

```bash
# List recent releases
fly releases -a wot-api | head -20

# Roll back to the previous version
fly releases rollback -a wot-api

# Or pin to a specific version
fly deploy --image registry.fly.io/wot-api:<previous-tag> -a wot-api
```

Verify:

```bash
curl https://wot.aixcelerator.app/api/v1/version
# Check git_sha matches the rolled-back commit
```

## Frontend rollback (Vercel)

```bash
# List recent deployments
vercel list worldoftaxonomy.com

# Promote a previous deployment to production
vercel promote <deployment-url>
```

Or in the Vercel dashboard: Deployments -> select previous green -> "Promote to Production."

Verify by loading `worldoftaxonomy.com` and checking the git commit in Vercel's deployment details.

## Database rollback

**Do not roll back DB schema changes without a planned migration down.**

- If a migration has already been applied and data has been written against it, rolling the app back without rolling the schema back is usually fine because schema changes are additive by convention (new columns are nullable, new tables are empty).
- If you must roll back a destructive schema change, your DB provider's point-in-time recovery (PITR) or a backup restore gets you to a timestamp. Check your window (Neon Free 30d, RDS up to 35d, Supabase varies, self-hosted = whatever your backup policy is). This is expensive and will drop everything newer. Only do it if the alternative is worse.

## After the rollback

1. **Post a status update** (internal channel at minimum).
2. **Open an incident doc** capturing the timeline.
3. **Diagnose** on a branch off the bad commit, not on `main`.
4. **Ship the fix** in a new deploy once tests pass locally + in CI.
5. **Do not revert the revert.** The original deploy is tainted until the fix is in.

## Postmortem checklist

- Time from first bad signal to rollback complete.
- Whether the regression was caught in CI (if yes, why it still landed; if no, what test would have caught it).
- Whether any data was written that the rolled-back code cannot read.
- Follow-ups: better staging env? Canary deploy? Feature flags for the class of change?
