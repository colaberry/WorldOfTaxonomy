# Runbook: Ingest failed

## Symptom

- `.github/workflows/ingest-refresh.yml` is red on its monthly run.
- A data consumer reports a known-new code (e.g. a 2026 NAICS addition) is missing.
- Stale-data warning in `/api/v1/systems/{id}` metadata (once the freshness field ships).

## Impact

- **Frontend** still serves the previous snapshot (ingest writes to `public`, frontend reads the same schema).
- **MCP + REST** continue to work against the last-known-good data.
- **Reputation risk**: freshness is part of the product promise.

## Detection

```bash
# Last successful ingest-refresh run
gh run list --workflow=ingest-refresh.yml --limit 5

# Detailed log for the failed run
gh run view <run-id> --log-failed

# Row counts per system (compare against expected in CLAUDE.md)
psql $DATABASE_URL -c "
  SELECT id, (SELECT count(*) FROM classification_node WHERE system_id = cs.id) AS nodes
  FROM classification_system cs
  ORDER BY id;"
```

## Diagnosis

| Failure mode | Signal | Fix direction |
|--------------|--------|---------------|
| Source URL 404 | `HTTPError: 404 Not Found` in the log | Upstream moved the file; update `ingest/<system>.py` |
| Source format changed | Parse error (xlrd, csv.Error, lxml) | Upstream schema drift; extend the ingester |
| DB write conflict | `UniqueViolationError`, `ForeignKeyViolationError` | Re-run is safe (idempotent); likely half-run state |
| Partial write (crashed mid-run) | Row count < expected | Re-run the single ingester: `python3 -m world_of_taxonomy ingest <system>` |
| Auth / network on GitHub Actions | `curl: (6)`, SSL errors | Re-run the workflow once; if it keeps failing investigate runner network |
| Crosswalk source (e.g. BLS concordance) changed shape | Edge count lower than baseline | Update the crosswalk ingester, not the system ingester |

## Mitigation

- **Do not** roll back the schema; ingest is always additive or idempotent per code.
- **Pin the source** if upstream is flapping: copy the current-known-good file to `data/` so the next run uses the local copy.
- **Disable the single failing ingester** in the workflow matrix if the rest of the batch is green.

## Remediation

1. Fix the ingester locally:
   ```bash
   python3 -m world_of_taxonomy ingest <system> --dry-run
   python3 -m pytest tests/test_ingest_<system>.py -v
   ```
2. Confirm row count, no duplicate codes, parent_code present for all non-top-level rows:
   ```bash
   psql $DATABASE_URL -c "
     SELECT count(*), count(DISTINCT code)
     FROM classification_node WHERE system_id = '<id>';"
   ```
3. Re-run `scripts/export_crosswalk_data.py` if the system participates in a crosswalk pair -- frontend SSR reads from the exported JSON.
4. Regenerate `frontend/public/llms-full.txt`:
   ```bash
   python3 scripts/build_llms_txt.py
   ```
5. Commit + deploy.

## Postmortem checklist

- Which system, which run.
- Root cause category (upstream change vs infra vs our bug).
- Was any data served with the gap? (Check frontend cache + CDN.)
- Follow-ups: does the ingest need a validator? Should we cache the upstream file in our own storage to decouple from URL flapping?
