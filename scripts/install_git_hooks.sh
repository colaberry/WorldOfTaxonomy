#!/usr/bin/env bash
# One-time setup: point this clone at the repo's .githooks/ directory so
# pre-push (and any future hooks) run automatically.
#
# Re-run is idempotent. Uninstall with: git config --unset core.hooksPath

set -euo pipefail

if [ ! -d ".githooks" ]; then
  echo "ERROR: run from the repo root (.githooks/ not found)" >&2
  exit 1
fi

git config core.hooksPath .githooks
chmod +x .githooks/pre-push

echo "Installed git hooks: core.hooksPath -> .githooks"
echo "Active hooks:"
ls -1 .githooks
