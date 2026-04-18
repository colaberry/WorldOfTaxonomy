#!/usr/bin/env bash
# Fail if any staged file contains the em-dash character (U+2014).
# Same check CI runs in .github/workflows/ci.yml, lifted into a
# pre-commit hook so violations never leave the laptop.

set -u

status=0
for file in "$@"; do
  [ -f "$file" ] || continue
  if grep -l $'\xe2\x80\x94' "$file" >/dev/null 2>&1; then
    echo "ERROR: em-dash (U+2014) found in $file. Use a hyphen - instead."
    status=1
  fi
done

exit "$status"
