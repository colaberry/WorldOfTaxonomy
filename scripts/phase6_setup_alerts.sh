#!/usr/bin/env bash
# Provision the Cloud Run alerting policies the launch-checklist
# Section 6 calls for:
#
#   1. 5xx rate > 1% over a 5-minute window.
#   2. Request latency p95 > 2s over a 5-minute window.
#   3. Instance restart loop (revision instance count fluctuating).
#
# Each alert posts to a notification channel that the script either
# discovers or creates. The default channel is email; pass
# --slack-webhook to wire a Slack channel as well.
#
# This script is idempotent: re-running it updates an existing policy
# instead of creating a duplicate.
#
# Usage:
#   ./scripts/phase6_setup_alerts.sh \
#       --project aixcelerator-prod \
#       --service wot-api \
#       --region  us-central1 \
#       --notify-email ops@aixcelerator.ai
#
#   # Optional: also post to Slack
#   ./scripts/phase6_setup_alerts.sh \
#       --project aixcelerator-prod --service wot-api --region us-central1 \
#       --notify-email ops@aixcelerator.ai \
#       --slack-webhook 'https://hooks.slack.com/services/...'
#
# Requires: gcloud (authenticated). See docs/handover/runbooks/
# for the response procedure when an alert fires.

set -euo pipefail

PROJECT=""
SERVICE=""
REGION=""
NOTIFY_EMAIL=""
SLACK_WEBHOOK=""

usage() {
    cat <<EOF
Usage: $0 --project P --service S --region R --notify-email E [options]

Required:
  --project        GCP project ID (e.g. aixcelerator-prod)
  --service        Cloud Run service name (e.g. wot-api)
  --region         Cloud Run region (e.g. us-central1)
  --notify-email   Email address to alert (creates a notification channel
                   if one does not already exist)

Optional:
  --slack-webhook URL    Also notify this Slack incoming-webhook URL
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)        PROJECT="$2"; shift 2 ;;
        --service)        SERVICE="$2"; shift 2 ;;
        --region)         REGION="$2"; shift 2 ;;
        --notify-email)   NOTIFY_EMAIL="$2"; shift 2 ;;
        --slack-webhook)  SLACK_WEBHOOK="$2"; shift 2 ;;
        -h|--help)        usage; exit 0 ;;
        *)                echo "unknown arg: $1" >&2; usage; exit 2 ;;
    esac
done
[[ -n "$PROJECT" && -n "$SERVICE" && -n "$REGION" && -n "$NOTIFY_EMAIL" ]] \
    || { usage; exit 2; }

red()    { printf '\033[31m%s\033[0m\n' "$*" >&2; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
step()   { echo; yellow "==> $1"; }

command -v gcloud >/dev/null 2>&1 || { red "gcloud not on PATH"; exit 2; }

# 1. Notification channels
step "Notification channels"
EMAIL_CHANNEL=$(gcloud alpha monitoring channels list \
    --project="$PROJECT" \
    --filter="type=email AND labels.email_address=$NOTIFY_EMAIL" \
    --format='value(name)' 2>/dev/null | head -1)

if [[ -z "$EMAIL_CHANNEL" ]]; then
    EMAIL_CHANNEL=$(gcloud alpha monitoring channels create \
        --project="$PROJECT" \
        --display-name="WoT ops: $NOTIFY_EMAIL" \
        --type=email \
        --channel-labels="email_address=$NOTIFY_EMAIL" \
        --format='value(name)')
    green "  created email channel: $EMAIL_CHANNEL"
else
    green "  reusing email channel: $EMAIL_CHANNEL"
fi

CHANNELS=("$EMAIL_CHANNEL")

if [[ -n "$SLACK_WEBHOOK" ]]; then
    SLACK_CHANNEL=$(gcloud alpha monitoring channels list \
        --project="$PROJECT" \
        --filter="type=slack" \
        --format='value(name)' 2>/dev/null | head -1)
    if [[ -z "$SLACK_CHANNEL" ]]; then
        SLACK_CHANNEL=$(gcloud alpha monitoring channels create \
            --project="$PROJECT" \
            --display-name="WoT ops: Slack" \
            --type=slack \
            --channel-labels="url=$SLACK_WEBHOOK" \
            --format='value(name)')
        green "  created slack channel: $SLACK_CHANNEL"
    else
        green "  reusing slack channel: $SLACK_CHANNEL"
    fi
    CHANNELS+=("$SLACK_CHANNEL")
fi

NOTIFY_FLAGS=()
for c in "${CHANNELS[@]}"; do
    NOTIFY_FLAGS+=(--notification-channels="$c")
done

# 2. Alert policies. Each is defined as a YAML body so re-running
# the script does an upsert (gcloud finds-by-display-name and patches).
emit_policy() {
    local name="$1" file="$2"
    local existing
    existing=$(gcloud alpha monitoring policies list \
        --project="$PROJECT" \
        --filter="displayName=\"$name\"" \
        --format='value(name)' 2>/dev/null | head -1)
    if [[ -n "$existing" ]]; then
        gcloud alpha monitoring policies update "$existing" \
            --project="$PROJECT" \
            --policy-from-file="$file" \
            "${NOTIFY_FLAGS[@]}" >/dev/null
        green "  updated: $name"
    else
        gcloud alpha monitoring policies create \
            --project="$PROJECT" \
            --policy-from-file="$file" \
            "${NOTIFY_FLAGS[@]}" >/dev/null
        green "  created: $name"
    fi
}

TMPDIR_=$(mktemp -d)
trap 'rm -rf "$TMPDIR_"' EXIT

step "Policy 1: 5xx rate > 1% (5-minute window)"
cat > "$TMPDIR_/p1.yaml" <<EOF
displayName: "WoT api: 5xx rate above 1%"
combiner: OR
conditions:
  - displayName: "5xx rate > 1% over 5 min"
    conditionThreshold:
      filter: |
        resource.type = "cloud_run_revision"
        AND resource.labels.service_name = "$SERVICE"
        AND metric.type = "run.googleapis.com/request_count"
        AND metric.labels.response_code_class = "5xx"
      comparison: COMPARISON_GT
      thresholdValue: 0.01
      duration: 300s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_RATE
documentation:
  content: |
    The Cloud Run service "$SERVICE" is returning 5xx responses at
    above 1% of total requests. Check the runbook at
    docs/handover/runbooks/api-5xx.md.
  mimeType: text/markdown
enabled: true
EOF
emit_policy "WoT api: 5xx rate above 1%" "$TMPDIR_/p1.yaml"

step "Policy 2: latency p95 > 2s (5-minute window)"
cat > "$TMPDIR_/p2.yaml" <<EOF
displayName: "WoT api: p95 latency above 2s"
combiner: OR
conditions:
  - displayName: "p95 latency > 2000ms over 5 min"
    conditionThreshold:
      filter: |
        resource.type = "cloud_run_revision"
        AND resource.labels.service_name = "$SERVICE"
        AND metric.type = "run.googleapis.com/request_latencies"
      comparison: COMPARISON_GT
      thresholdValue: 2000
      duration: 300s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_PERCENTILE_95
documentation:
  content: |
    The Cloud Run service "$SERVICE" has p95 latency above 2 seconds.
    Common causes: cold starts on a new revision, slow database
    queries, upstream 3rd-party hangs. See
    docs/handover/runbooks/cloud-run-cold-start-spike.md and
    docs/handover/runbooks/key-validation-slow.md.
  mimeType: text/markdown
enabled: true
EOF
emit_policy "WoT api: p95 latency above 2s" "$TMPDIR_/p2.yaml"

step "Policy 3: revision restart loop"
cat > "$TMPDIR_/p3.yaml" <<EOF
displayName: "WoT api: revision restart loop"
combiner: OR
conditions:
  - displayName: "instance count churn over 5 min"
    conditionThreshold:
      filter: |
        resource.type = "cloud_run_revision"
        AND resource.labels.service_name = "$SERVICE"
        AND metric.type = "run.googleapis.com/container/instance_count"
      comparison: COMPARISON_GT
      thresholdValue: 5
      duration: 300s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_DELTA
documentation:
  content: |
    The Cloud Run service "$SERVICE" instance count is changing
    rapidly, indicating a possible startup/crash loop. See
    docs/handover/runbooks/api-5xx.md (the "container won't start"
    section) and check Cloud Logging for fatal errors at boot.
  mimeType: text/markdown
enabled: true
EOF
emit_policy "WoT api: revision restart loop" "$TMPDIR_/p3.yaml"

step "VERIFY"
gcloud alpha monitoring policies list \
    --project="$PROJECT" \
    --filter="displayName ~ ^WoT api:" \
    --format="table(displayName,enabled)"

echo
green "Section 6 alerts: complete."
green ""
green "Test the wiring by triggering Sentry's smoke endpoint or by"
green "deliberately scaling the service to 0 instances briefly."
