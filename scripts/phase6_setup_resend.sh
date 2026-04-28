#!/usr/bin/env bash
# Provision the Phase 6 Resend secret in GCP Secret Manager and wire
# it to the Cloud Run service.
#
# What this does:
#   1. Validates the secret format (Resend keys start with `re_`).
#   2. Creates the `resend-api-key` secret in Secret Manager if it
#      does not already exist (versioned; rotating later is one
#      `gcloud secrets versions add` call).
#   3. Stores the new value as a fresh version.
#   4. Grants the Cloud Run service account
#      `roles/secretmanager.secretAccessor` on the secret.
#   5. Updates the Cloud Run service to expose the secret as
#      `RESEND_API_KEY` env var.
#
# Usage:
#   ./scripts/phase6_setup_resend.sh \
#       --project aixcelerator-prod \
#       --service wot-api \
#       --region  us-central1
#
# Requires: gcloud (authenticated). The Resend API key is read
# interactively from a TTY so it never lives in shell history.

set -euo pipefail

PROJECT=""
SERVICE=""
REGION=""
SECRET_NAME="resend-api-key"
ENV_VAR_NAME="RESEND_API_KEY"
SENDER_NAME="resend-sender"
SENDER_EMAIL="${SENDER_EMAIL:-noreply@aixcelerator.ai}"

usage() {
    cat <<EOF
Usage: $0 --project P --service S --region R [--secret-name N] [--env-var V]

  --project     GCP project ID (e.g. aixcelerator-prod)
  --service     Cloud Run service name (e.g. wot-api)
  --region      Cloud Run region (e.g. us-central1)
  --secret-name Override the Secret Manager name (default: $SECRET_NAME)
  --env-var     Override the env var name on Cloud Run (default: $ENV_VAR_NAME)

Optional:
  SENDER_EMAIL env var  Default sender shown in From: (default: $SENDER_EMAIL)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)     PROJECT="$2"; shift 2 ;;
        --service)     SERVICE="$2"; shift 2 ;;
        --region)      REGION="$2"; shift 2 ;;
        --secret-name) SECRET_NAME="$2"; shift 2 ;;
        --env-var)     ENV_VAR_NAME="$2"; shift 2 ;;
        -h|--help)     usage; exit 0 ;;
        *)             echo "unknown arg: $1" >&2; usage; exit 2 ;;
    esac
done
[[ -n "$PROJECT" && -n "$SERVICE" && -n "$REGION" ]] || { usage; exit 2; }

red()    { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
step()   { echo; yellow "==> $1"; }

command -v gcloud >/dev/null 2>&1 || { red "gcloud not on PATH"; exit 2; }

# 1. Read the key from TTY (never echo, never store in history)
step "Read Resend API key"
[[ -t 0 ]] || { red "stdin must be a TTY (paste the key when prompted)"; exit 2; }
read -r -s -p "Paste Resend API key (input hidden): " RESEND_KEY
echo
[[ -n "$RESEND_KEY" ]] || { red "empty"; exit 1; }
if [[ "$RESEND_KEY" != re_* ]]; then
    red "Resend keys start with 're_'. Got prefix: ${RESEND_KEY:0:5}..."
    exit 1
fi
green "  format check: OK"

# 2. Create the secret if missing
step "Ensure secret exists"
if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT" >/dev/null 2>&1; then
    green "  $SECRET_NAME already exists; will add a new version"
else
    gcloud secrets create "$SECRET_NAME" \
        --project="$PROJECT" \
        --replication-policy=automatic \
        --labels="env=prod,phase=phase6" \
        >/dev/null
    green "  created $SECRET_NAME"
fi

# 3. Add new version
step "Add new secret version"
echo -n "$RESEND_KEY" | gcloud secrets versions add "$SECRET_NAME" \
    --project="$PROJECT" \
    --data-file=- \
    >/dev/null
green "  new version added"
unset RESEND_KEY  # purge from this shell

# 4. Grant Cloud Run service account access
step "Grant Cloud Run SA secret access"
SA_EMAIL=$(gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(spec.template.spec.serviceAccountName)')
[[ -n "$SA_EMAIL" ]] || {
    SA_EMAIL=$(gcloud projects describe "$PROJECT" \
        --format='value(projectNumber)')-compute@developer.gserviceaccount.com
    yellow "  service account not pinned on Cloud Run; using default compute SA: $SA_EMAIL"
}
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
    --project="$PROJECT" \
    --member="serviceAccount:$SA_EMAIL" \
    --role=roles/secretmanager.secretAccessor \
    >/dev/null
green "  $SA_EMAIL -> roles/secretmanager.secretAccessor on $SECRET_NAME"

# 5. Wire the env var on Cloud Run
step "Update Cloud Run service"
gcloud run services update "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --update-secrets="${ENV_VAR_NAME}=${SECRET_NAME}:latest" \
    --update-env-vars="RESEND_SENDER=$SENDER_EMAIL" \
    >/dev/null
green "  $SERVICE now exposes $ENV_VAR_NAME from $SECRET_NAME:latest"

# 6. Verify by inspecting the active revision
step "Verify"
ACTIVE_REV=$(gcloud run services describe "$SERVICE" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(status.latestReadyRevisionName)')
green "  active revision: $ACTIVE_REV"
gcloud run revisions describe "$ACTIVE_REV" \
    --project="$PROJECT" --region="$REGION" \
    --format='value(spec.containers[0].env)' \
    | grep -F "name=$ENV_VAR_NAME" \
    && green "  $ENV_VAR_NAME visible on the active revision" \
    || { red "FAIL: $ENV_VAR_NAME not visible on revision"; exit 1; }

echo
green "Resend setup: complete."
green ""
green "Next step: send a test mail by hitting the /api/v1/developers/signup"
green "endpoint with your own email; the magic link should arrive within 30s."
