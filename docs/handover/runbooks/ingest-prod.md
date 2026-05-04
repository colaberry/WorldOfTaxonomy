# Runbook: inject data into prod via the ingest pipeline

This is the one-command path that runs **after** any PR that ships new data
content (description backfills, structural ingesters for new systems,
crosswalks, ad-hoc data refreshes, ...).

It replaces the prior workflow of producing a local Postgres dump and
running `pg_restore --clean` against prod.

> **TL;DR:** after a backfill PR merges to main and Cloud Build deploys:
>
> ```bash
> ./scripts/ingest-prod.sh anzsic_2006 soc_2018
> ```

---

## How it works

```
developer laptop
   │
   ├── ./scripts/ingest-prod.sh anzsic_2006 soc_2018
   │     └── triggers Cloud Run Job 'wot-ingest' with INGEST_TASKS env override
   │
   ▼
Cloud Run Job 'wot-ingest'
   image  : us-east1-docker.pkg.dev/colaberry-wot/wot-repo/wot-api:latest
   secrets: DATABASE_URL (prod), JWT_SECRET
   command: bash scripts/run_ingest_tasks.sh
   │
   └── reads scripts/ingest_manifest.json, dispatches each task ID
   │
   ▼
Cloud SQL (prod)
   classification_node.description columns get populated where they were NULL.
   Idempotent re-runs are safe; apply_descriptions() only touches NULL/empty rows
   and structural ingesters use INSERT ... ON CONFLICT DO NOTHING.
```

The manifest, runner, and wrapper live in the same repo so reviewers can
audit them on every PR.

---

## Prerequisites

- `gcloud` CLI authenticated as a principal with `run.jobs.run` on
  the `colaberry-wot` GCP project.
- The PR has merged to `main` AND the matching Cloud Build run finished
  successfully (so the latest wot-api image is available in Artifact
  Registry). Confirm at:
  https://console.cloud.google.com/cloud-build/builds?project=colaberry-wot

---

## The four common scenarios

### 1. After a description-backfill PR (the most common case)

Ram pushes a PR that adds `scripts/backfill_<system>_descriptions.py`
plus a one-line entry in `scripts/ingest_manifest.json`:

```json
"<system>": ["python scripts/backfill_<system>_descriptions.py"]
```

After merge:

```bash
./scripts/ingest-prod.sh <system>
```

If multiple systems landed in one PR or multiple PRs in a batch:

```bash
./scripts/ingest-prod.sh anzsic_2006 soc_2018 mesh icd_11
```

Tasks run sequentially. The runner stops on the first non-zero exit so
a single failure surfaces immediately.

### 2. After adding a brand-new classification system

The PR adds a structural ingester (`world_of_taxonomy/ingest/<new>.py`)
that exposes `python -m world_of_taxonomy ingest <new>`. Add a manifest
entry:

```json
"<new>": ["python -m world_of_taxonomy ingest <new>"]
```

Then:

```bash
./scripts/ingest-prod.sh <new>
```

### 3. After adding a crosswalk

```json
"<src>_<dst>_crosswalk": ["python -m world_of_taxonomy ingest crosswalk_<src>_<dst>"]
```

Run:

```bash
./scripts/ingest-prod.sh <src>_<dst>_crosswalk
```

### 4. Custom ad-hoc data sync

Anything expressible as a shell command works. Add an entry, run it.
Example:

```json
"labor_market_2026_q2": ["python scripts/refresh_lm_2026_q2.py"]
```

```bash
./scripts/ingest-prod.sh labor_market_2026_q2
```

---

## Adding a new task (one-line PR addition)

1. In `scripts/ingest_manifest.json`, add a key (snake_case, lowercase) at
   the appropriate alphabetical position. Value is an ordered list of
   shell commands. Keep `python scripts/<file>.py` form when possible
   (the integrity check validates the file exists).
2. Make sure each command is **idempotent** (safe to re-run).
3. Run `python3 scripts/check_manifest_integrity.py` locally to confirm
   the manifest still parses + every referenced script exists.
4. Mention in the PR description: "Run after merge: `./scripts/ingest-prod.sh <new_task_id>`."

---

## Inspecting / listing tasks

```bash
./scripts/ingest-prod.sh --list
```

Prints every available task ID and how many commands it runs.

---

## Verifying a populated row after a run

```bash
# Pick any code from the system you ingested.
curl -s https://wot.aixcelerator.ai/api/v1/systems/anzsic_2006/nodes/A | jq .description
```

Or via Cloud SQL Auth Proxy + psql for bulk spot-checks (see
`docs/handover/runbooks/db-down.md` for the proxy command).

---

## Troubleshooting

### `unknown task ID(s)`

The wrapper validates the task IDs against the manifest **before** firing
the job. Run `./scripts/ingest-prod.sh --list` to see all available IDs;
they're case-sensitive.

### Job runs but `description` columns still NULL

Most likely the task you ran does not actually map to those rows. Check
the script's `_SYSTEM_ID` constant against the rows you spot-checked.

### Job fails with `connect ECONNREFUSED` / `password authentication failed`

The Cloud Run Job uses the `DATABASE_URL` secret in Secret Manager. If
that secret was rotated, the Job picks up the new value automatically on
its next execution (no rebuild needed). If the failure persists, confirm
the latest secret version is still active:

```bash
gcloud secrets versions list DATABASE_URL --project=colaberry-wot
```

### Job times out

Default Cloud Run Job timeout is 1 hour. If you queued a large set of
tasks and exceeded that, split the run:

```bash
./scripts/ingest-prod.sh task_a task_b
./scripts/ingest-prod.sh task_c task_d
```

Or override the timeout:

```bash
gcloud run jobs update wot-ingest \
  --region=us-east1 --project=colaberry-wot \
  --task-timeout=2h
```

### Need to roll back a run

`apply_descriptions()` is NULL-only; it never overwrites existing data.
A re-run is safe. If a structural ingester wrote bad rows, restore from
the most recent prod backup using the documented rollback playbook in
`docs/handover/runbooks/deploy-rollback.md` (the same `wot-restore-*`
Cloud Run Job pattern).

---

## Why this shape (vs auto-trigger on every push)

Per the project owner's preference, this is a **manual one-command**
runbook (not auto-triggered on every push to main). Rationale:

- Some backfill scripts are slow or hit rate-limited upstream APIs;
  running them on every PR-merge would compound those costs.
- Manual gives a clean human checkpoint: "deploy is green, now I run
  the data step."
- Mirrors the rhythm of database migrations: schema is auto-applied,
  data refresh is one command.

If/when the team wants full automation, the same manifest works under a
Cloud Build path-filter step that triggers on `scripts/backfill_**` or
`world_of_taxonomy/ingest/**` changes.

---

## See also

- [docs/handover/cicd-deployment.md](../cicd-deployment.md) - how the rest of the pipeline is wired
- [docs/handover/description-backfill.md](../description-backfill.md) - the cumulative description-backfill effort across PRs #50 - #78
- [scripts/ingest_manifest.json](../../../scripts/ingest_manifest.json) - the live task list
- [scripts/check_manifest_integrity.py](../../../scripts/check_manifest_integrity.py) - CI validator
- [scripts/run_ingest_tasks.sh](../../../scripts/run_ingest_tasks.sh) - in-container runner
- [scripts/ingest-prod.sh](../../../scripts/ingest-prod.sh) - host-side wrapper
