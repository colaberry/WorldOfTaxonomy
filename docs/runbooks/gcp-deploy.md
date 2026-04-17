# GCP Cloud Run Deploy Runbook

Production hosting for WorldOfTaxonomy on GCP:

| Component | Resource |
|---|---|
| GCP project | `colaberry-wot` |
| Region | `us-east1` |
| Backend | Cloud Run service `wot-api` (FastAPI, port 8000) |
| Frontend | Cloud Run service `wot-web` (Next.js, port 3000) |
| Database | Cloud SQL `wot-db` (PostgreSQL 15, `db-f1-micro`) |
| Image registry | Artifact Registry `wot-repo` |
| Secrets | Secret Manager: `DATABASE_URL`, `JWT_SECRET`, `REPORT_EMAIL` |
| CI/CD | Cloud Build trigger `wot-main-deploy` on push to `main` |

## One-time infrastructure setup

Run as a GCP project Owner (Cloud Shell or local with `gcloud auth login`):

```bash
PROJECT=colaberry-wot
REGION=us-east1
BILLING_ACCOUNT=$(gcloud billing accounts list --format='value(name)' | head -n1)

# 1. Project + billing
gcloud projects create "$PROJECT" --name="Colaberry WorldOfTaxonomy"
gcloud billing projects link "$PROJECT" --billing-account="$BILLING_ACCOUNT"
gcloud config set project "$PROJECT"

# 2. APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com

# 3. Artifact Registry
gcloud artifacts repositories create wot-repo \
  --repository-format=docker --location="$REGION" \
  --description="WorldOfTaxonomy images"

# 4. Cloud SQL (db-f1-micro ~ $9/mo with 10GB storage)
gcloud sql instances create wot-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region="$REGION" \
  --storage-size=10GB --storage-type=SSD \
  --backup-start-time=07:00
gcloud sql databases create worldoftaxonomy --instance=wot-db
DB_PASS="$(openssl rand -hex 16)"
gcloud sql users create wot --instance=wot-db --password="$DB_PASS"
echo "DB password (save this): $DB_PASS"

# 5. Secrets
INSTANCE_CONN="$PROJECT:$REGION:wot-db"
printf 'postgresql://wot:%s@/worldoftaxonomy?host=/cloudsql/%s' "$DB_PASS" "$INSTANCE_CONN" \
  | gcloud secrets create DATABASE_URL --data-file=-
python3 -c 'import secrets; print(secrets.token_hex(32))' \
  | gcloud secrets create JWT_SECRET --data-file=-
printf 'ram@colaberry.com' | gcloud secrets create REPORT_EMAIL --data-file=-

# 6. IAM
PROJECT_NUM=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
CB_SA="${PROJECT_NUM}@cloudbuild.gserviceaccount.com"
RUN_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

for ROLE in run.admin artifactregistry.writer iam.serviceAccountUser \
            secretmanager.secretAccessor cloudsql.client; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$CB_SA" --role="roles/$ROLE"
done
for ROLE in secretmanager.secretAccessor cloudsql.client; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="serviceAccount:$RUN_SA" --role="roles/$ROLE"
done

# 7. Cloud Build GitHub trigger
# NOTE: first-time only — connect the Cloud Build GitHub App to
# colaberry/WorldOfTaxonomy via https://console.cloud.google.com/cloud-build/triggers
# then run:
gcloud builds triggers create github \
  --repo-owner=colaberry \
  --repo-name=WorldOfTaxonomy \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --name=wot-main-deploy \
  --substitutions="_REGION=$REGION,_REPO=wot-repo,_INSTANCE_CONN=$INSTANCE_CONN"
```

## Normal deploys

Merge to `main` → trigger fires automatically. Watch:

```bash
gcloud builds list --ongoing
gcloud builds log <BUILD_ID>
```

## Manual deploy (bypass CI)

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions="_REGION=us-east1,_REPO=wot-repo,_INSTANCE_CONN=colaberry-wot:us-east1:wot-db,SHORT_SHA=$(git rev-parse --short HEAD)"
```

## Service URLs

```bash
gcloud run services list --region=us-east1
```

## Logs

```bash
gcloud run services logs tail wot-api --region=us-east1
gcloud run services logs tail wot-web --region=us-east1
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service=wot-api --region=us-east1

# Roll all traffic to a prior revision
gcloud run services update-traffic wot-api \
  --to-revisions=<REVISION_NAME>=100 --region=us-east1
```

## Secret rotation

```bash
# Add a new version; latest is picked up on next Cloud Run revision
printf 'new-value' | gcloud secrets versions add DATABASE_URL --data-file=-
# Force a new revision so the service reads the new version:
gcloud run services update wot-api --region=us-east1 \
  --update-secrets=DATABASE_URL=DATABASE_URL:latest
```

## Cost controls

Cloud SQL is the dominant cost (~$9/mo at idle). To pause billing while preserving data:

```bash
# Stop DB (storage still billed, compute paused)
gcloud sql instances patch wot-db --activation-policy=NEVER
# Resume
gcloud sql instances patch wot-db --activation-policy=ALWAYS
```

Set a budget alert:

```bash
# Via console: Billing -> Budgets & alerts -> Create budget
# Threshold: $15, email: coredev@colaberry.com
```

If the $5/mo target is hard, migrate DB to **Neon free tier** (0.5 GB Postgres):

1. Create a Neon project at https://neon.tech → get `postgresql://...` URL with `?sslmode=require`.
2. Update secret: `printf '<NEON_URL>' | gcloud secrets versions add DATABASE_URL --data-file=-`
3. Remove Cloud SQL attachment from backend:
   ```bash
   gcloud run services update wot-api --region=us-east1 \
     --clear-cloudsql-instances
   ```
4. Delete Cloud SQL instance: `gcloud sql instances delete wot-db`

## Architecture notes

- **Database connection:** backend reaches Cloud SQL over a Unix socket mounted at `/cloudsql/$PROJECT:$REGION:wot-db` — enabled by the `--add-cloudsql-instances` flag. No VPC connector, no public IP.
- **Schema init:** `Dockerfile.backend` runs `python3 -m world_of_taxonomy init` on every container start. This must remain idempotent — each cold start retries it.
- **Data ingestion:** ingest jobs are **not** part of Cloud Run. Run locally (or via a one-off Cloud Run Job) pointing at the same Cloud SQL instance — e.g. `DATABASE_URL=... python3 -m world_of_taxonomy ingest <system>`.
- **Frontend build context:** `cloudbuild.yaml` builds the frontend from the **repo root** (not `frontend/`), because `frontend/package.json`'s `prebuild` script copies sibling `wiki/`, `blog/`, and `crosswalk-data/` into `src/content` before `next build`. The production image is `frontend/Dockerfile.prod`; `frontend/Dockerfile` is unchanged and remains the local `docker-compose` dev image.
- **Frontend → backend routing:** `next.config.ts` rewrites `/api/*` to `$BACKEND_URL/api/*`. The deploy step looks up `wot-api`'s Cloud Run URL and injects it as `BACKEND_URL`.
