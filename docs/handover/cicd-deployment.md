# CI/CD & Deployment Handover

Starter doc for whoever owns the WorldOfTaxonomy deploy pipeline. It answers: what ships where, what triggers a deploy, where the knobs are, and what to read next.

Deep dives you will need:
- Full GCP setup commands: [docs/handover/runbooks/gcp-deploy.md](runbooks/gcp-deploy.md)
- Rollback playbook: [docs/handover/runbooks/deploy-rollback.md](runbooks/deploy-rollback.md)
- DB outage playbook: [docs/handover/runbooks/db-down.md](runbooks/db-down.md)
- Migration playbook: [docs/handover/runbooks/migrations.md](runbooks/migrations.md)
- Ingest-refresh playbook: [docs/handover/runbooks/ingest-failed.md](runbooks/ingest-failed.md)
- Inject data into prod (one-command runbook for backfill PRs): [docs/handover/runbooks/ingest-prod.md](runbooks/ingest-prod.md)
- Architecture overview: [docs/handover/backend.md](backend.md), [docs/handover/frontend.md](frontend.md)

---

## 1. What gets deployed

| Service | Image | Runtime | Port | Source |
|---|---|---|---|---|
| `wot-api` | `${REGION}-docker.pkg.dev/${PROJECT}/wot-repo/wot-api` | Cloud Run (FastAPI + uvicorn) | 8000 | [Dockerfile.backend](../../Dockerfile.backend) |
| `wot-web` | `${REGION}-docker.pkg.dev/${PROJECT}/wot-repo/wot-web` | Cloud Run (Next.js 16) | 3000 | [frontend/Dockerfile.prod](../../frontend/Dockerfile.prod) |
| `wot-db` | n/a | Cloud SQL Postgres 15, `db-f1-micro` | 5432 (unix socket) | schema init on container start |

The frontend proxies `/api/*` to the backend via a Next.js rewrite; the backend URL is injected as `BACKEND_URL` at deploy time.

Domains (see memory `project_deployment_plan`):
- Frontend: `worldoftaxonomy.com` (served from `wot-web`)
- API/MCP: `wot.aixcelerator.ai` (served from `wot-api`)

---

## 2. Pipeline at a glance

```
Push to main on colaberry/WorldOfTaxonomy
        |
        v
GitHub Actions CI (.github/workflows/ci.yml)     <- tests + typecheck + em-dash + llms-full.txt freshness
        |
        v  (green required)
Cloud Build trigger "wot-main-deploy"            <- cloudbuild.yaml
        |
        +---- build wot-api image  ----+
        |                              |
        +---- build wot-web image  ----+
                                       |
                                       v
                          push images to Artifact Registry
                                       |
                                       v
                          gcloud run deploy wot-api  (with Cloud SQL + secrets)
                                       |
                                       v
                          gcloud run deploy wot-web  (with BACKEND_URL set from wot-api URL)
```

Build config: [cloudbuild.yaml](../../cloudbuild.yaml). Typical build time is ~6-10 minutes.

### CI jobs that gate merges (.github/workflows/)

| Workflow | Triggers | What it checks |
|---|---|---|
| `ci.yml` | push + PR to main | pytest (backend) with coverage, TypeScript typecheck, frontend build, `npm audit`, em-dash ban, `llms-full.txt` freshness |
| `security.yml` | scheduled | dependency scanning |
| `ingest-refresh.yml` | scheduled / manual | runs ingest jobs that hit external sources |
| `post-merge-refresh.yml` | push to main | post-merge data refresh hooks |
| `release.yml` | tag push | release artifact build |

CI does **not** deploy. Deploys come from Cloud Build, gated on CI green via the trigger's branch filter (`^main$`) plus repo branch protection.

---

## 3. Required GCP resources (already provisioned)

Inherited state - do not recreate blind:

| Resource | Value |
|---|---|
| GCP project | `colaberry-wot` |
| Region | `us-east1` |
| Artifact Registry repo | `wot-repo` (Docker format) |
| Cloud SQL instance | `wot-db` (Postgres 15, `db-f1-micro`, 10 GB SSD) |
| Cloud SQL connection name | `colaberry-wot:us-east1:wot-db` |
| Secrets (Secret Manager) | `DATABASE_URL`, `JWT_SECRET`, `REPORT_EMAIL` |
| Cloud Build trigger | `wot-main-deploy` |

Cloud Build trigger substitutions (set on the trigger, not in the yaml):

```
_REGION         = us-east1
_REPO           = wot-repo
_INSTANCE_CONN  = colaberry-wot:us-east1:wot-db
```

### Service account permissions

Cloud Build SA (`${PROJECT_NUM}@cloudbuild.gserviceaccount.com`):
- `roles/run.admin`
- `roles/artifactregistry.writer`
- `roles/iam.serviceAccountUser`
- `roles/secretmanager.secretAccessor`
- `roles/cloudsql.client`

Cloud Run SA (`${PROJECT_NUM}-compute@developer.gserviceaccount.com`):
- `roles/secretmanager.secretAccessor`
- `roles/cloudsql.client`

---

## 4. Day-to-day operations

### Deploy a change
```
Open PR -> CI green -> merge to main -> Cloud Build trigger fires automatically.
```

Watch a build:
```bash
gcloud builds list --ongoing
gcloud builds log <BUILD_ID>
```

### Tail service logs
```bash
gcloud run services logs tail wot-api --region=us-east1
gcloud run services logs tail wot-web --region=us-east1
```

### Get service URLs
```bash
gcloud run services list --region=us-east1
```

### Health checks
- Backend: `GET https://wot.aixcelerator.ai/api/v1/healthz`
- Frontend: `GET https://worldoftaxonomy.com/` (200 + HTML)
- Docs pass-through: `GET https://worldoftaxonomy.com/llms-full.txt` (plain text)
- MCP check: Claude Desktop connects and lists **26 tools**

### Manual (out-of-band) deploy
Use this only for a hotfix when CI is red for an unrelated reason and you've vetted the risk:

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions="_REGION=us-east1,_REPO=wot-repo,_INSTANCE_CONN=colaberry-wot:us-east1:wot-db,SHORT_SHA=$(git rev-parse --short HEAD)"
```

### Rollback
List revisions, shift traffic:
```bash
gcloud run revisions list --service=wot-api --region=us-east1
gcloud run services update-traffic wot-api \
  --to-revisions=<REVISION>=100 --region=us-east1
```
Repeat for `wot-web`. Full procedure in [docs/handover/runbooks/deploy-rollback.md](runbooks/deploy-rollback.md).

### Secret rotation
```bash
printf 'new-value' | gcloud secrets versions add DATABASE_URL --data-file=-
gcloud run services update wot-api --region=us-east1 \
  --update-secrets=DATABASE_URL=DATABASE_URL:latest
```
Cloud Run needs a new revision for the rotated secret to take effect; the `update` above forces one.

---

## 5. Things that are NOT automated (watch for these)

1. **Data ingestion.** Ingest jobs do **not** run in Cloud Run. They are one-off scripts, executed either locally or via a Cloud Run Job pointed at the same `DATABASE_URL`. Example: `DATABASE_URL=... python3 -m world_of_taxonomy ingest <system>`. See [docs/adding-a-new-system.md](../adding-a-new-system.md) and [docs/handover/runbooks/ingest-failed.md](runbooks/ingest-failed.md).
2. **Schema init vs migrations.** The backend container calls `python3 -m world_of_taxonomy init` on every cold start; it must stay idempotent. Non-idempotent schema changes go through Alembic under [migrations/](../../migrations/). See [docs/handover/runbooks/migrations.md](runbooks/migrations.md).
3. **Frontend build context.** `cloudbuild.yaml` builds the web image from the **repo root**, not `frontend/`, because `frontend/package.json`'s `prebuild` hook copies sibling `wiki/`, `blog/`, `crosswalk-data/`, and `tree-data/` into `src/content` before `next build`. Do not "fix" the build context to `frontend/`.
4. **`llms-full.txt` freshness.** CI rebuilds it and fails if the committed copy is stale. When wiki content changes, run `python scripts/build_llms_txt.py` locally and commit the result.
5. **Em-dash ban.** CI greps for U+2014 across `.py`, `.md`, `.ts`, `.tsx`, `.sql`. Use a hyphen `-`.

---

## 6. Authentication (current state vs roadmap)

**Today**: magic-link cookie session. Sign-in is by emailing a single-use link via Resend; the callback at `GET /api/v1/auth/magic-callback?t=...` sets `dev_session` (httponly JWT, 60-min TTL) + `wot_csrf` (JS-readable double-submit token). Sign-out via `POST /api/v1/auth/logout`. JWT signature secret in `JWT_SECRET`. Password sign-in and OAuth (GitHub/Google/LinkedIn) were both removed in 2026-04-30 - the magic-link flow is the only authenticated entry point on the public site.

**Planned migration** (not implemented yet): central IdP at `auth.aixcelerator.ai` using **Zitadel Cloud** for authN plus **Permit.io** for authZ. When this lands, the backend switches from HS256 local JWT verification to RS256 JWKS against Zitadel, and per-operation checks move to `permit.check(user, action, resource)`. See [docs/handover/portfolio-auth.md](portfolio-auth.md). Do not plan pipeline changes around this until the migration plan is green-lit.

---

## 7. Cost controls

Cloud SQL (`db-f1-micro`) is the dominant cost (~$9/mo at idle). Levers:

- Pause the DB without losing data: `gcloud sql instances patch wot-db --activation-policy=NEVER`
- Resume: `gcloud sql instances patch wot-db --activation-policy=ALWAYS`
- Budget alert: Billing -> Budgets & alerts -> set $15 threshold, email `dev@colaberry.com`

A longer-term alternative documented in [gcp-deploy.md](runbooks/gcp-deploy.md) is to migrate to Neon free tier and drop Cloud SQL entirely.

---

## 8. Onboarding checklist for a new CICD owner

- [ ] Request `roles/editor` (or narrower: `roles/run.admin` + `roles/cloudbuild.builds.editor` + `roles/secretmanager.admin`) on `colaberry-wot` from the project owner
- [ ] `gcloud auth login && gcloud config set project colaberry-wot`
- [ ] Verify access: `gcloud run services list --region=us-east1` lists `wot-api` and `wot-web`
- [ ] Verify access: `gcloud builds list --limit=5` shows recent builds
- [ ] Verify access: `gcloud secrets list` shows the three secrets
- [ ] Trigger a manual no-op deploy on a branch PR to confirm CI + Cloud Build path end-to-end
- [ ] Read the runbooks under `docs/handover/runbooks/`
- [ ] Confirm you can tail logs from both services
- [ ] Confirm rollback works on a throwaway revision

---

## 9. Who to contact

| Topic | Person |
|---|---|
| Product / priorities | Ram Katamaraja (`dev@colaberry.com`) |
| GCP project ownership | Ram Katamaraja |
| Repo admin on GitHub | Ram Katamaraja |
| Report / abuse email (public) | `REPORT_EMAIL` secret |
