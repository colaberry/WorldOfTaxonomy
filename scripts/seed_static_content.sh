#!/usr/bin/env bash
# Regenerate static AEO/RAG content from the local DB and commit it.
#
# Use this for the initial 1,000-system seed and any time you want a
# one-shot "refresh + commit" without remembering the four manual steps.
# The pre-push hook in .githooks/pre-push handles per-push drift; this
# script handles deliberate batch refreshes.
#
# Behavior:
#   1. Refuses to run on main (commit through a feature branch + PR).
#   2. Runs the regen.
#   3. If no drift, exits 0 without making a commit.
#   4. If drift, stages frontend/public/llms-codes/ and creates one
#      commit on the current branch.
#   5. Push is opt-in (--push), never automatic.
#
# Usage:
#   bash scripts/seed_static_content.sh                   # regen + commit
#   bash scripts/seed_static_content.sh --push            # regen + commit + push
#   bash scripts/seed_static_content.sh --message "..."   # custom commit message

set -euo pipefail

PUSH=0
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --message) MESSAGE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"

current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo "")"
if [ -z "$current_branch" ]; then
  echo "[seed] not on a branch (detached HEAD); refusing." >&2
  exit 1
fi
if [ "$current_branch" = "main" ] || [ "$current_branch" = "master" ]; then
  echo "[seed] refusing to commit directly to $current_branch." >&2
  echo "[seed] Switch to a feature branch first, e.g.:" >&2
  echo "[seed]   git switch -c chore/seed-static-content" >&2
  exit 1
fi

if ! git diff --quiet -- frontend/public/llms-codes/ \
   || ! git diff --cached --quiet -- frontend/public/llms-codes/; then
  echo "[seed] frontend/public/llms-codes/ already has uncommitted changes." >&2
  echo "[seed] Commit or stash those before re-running." >&2
  exit 1
fi

echo "[seed] regenerating static content (build_static_content.py)..."
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
"$PYTHON_BIN" scripts/build_static_content.py

untracked="$(git ls-files --others --exclude-standard -- frontend/public/llms-codes/ 2>/dev/null || true)"
if git diff --quiet -- frontend/public/llms-codes/ \
   && git diff --cached --quiet -- frontend/public/llms-codes/ \
   && [ -z "$untracked" ]; then
  echo "[seed] no drift; nothing to commit."
  exit 0
fi

file_count="$(git status --short -- frontend/public/llms-codes/ | wc -l | tr -d ' ')"
size="$(du -sh frontend/public/llms-codes/ | cut -f1)"
echo "[seed] drift detected:"
echo "[seed]   branch: $current_branch"
echo "[seed]   files:  $file_count"
echo "[seed]   size:   $size"

if [ -z "$MESSAGE" ]; then
  MESSAGE="regen(static): refresh llms-codes from DB ($file_count files, $size)"
fi

git add frontend/public/llms-codes/
git commit -m "$MESSAGE"

if [ "$PUSH" -eq 1 ]; then
  echo "[seed] pushing $current_branch..."
  git push
  echo "[seed] done. Open a PR to land on main."
else
  echo "[seed] committed on $current_branch (not pushed)."
  echo "[seed] Push with: git push"
fi
