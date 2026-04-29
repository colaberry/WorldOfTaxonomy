"""Detect API keys that have not been used in N days.

Two modes:
  - Default (alert-only): print a report. Exit 0. Schedule via Cloud
    Scheduler -> Cloud Run Job, weekly. Pipe stdout to a Slack webhook
    or email if you want active notification; the script intentionally
    stays passive so the operator decides what to do.
  - --revoke: revoke each abandoned key in place with
    `revoked_reason = 'abandoned_<days>d'`. Use after a grace period
    where the operator has already had a chance to review the report.

A key is "abandoned" when:
  - revoked_at IS NULL (still live)
  - last_used_at < NOW() - INTERVAL <days> days
    OR last_used_at IS NULL AND created_at < NOW() - INTERVAL <days> days

Newly-issued never-used keys hit the second arm only after the grace
window, so a key minted yesterday and never called does not get
flagged in a 180-day audit.

Usage:
    DATABASE_URL=postgres://... python scripts/audit_abandoned_keys.py
    DATABASE_URL=postgres://... python scripts/audit_abandoned_keys.py --days 180
    DATABASE_URL=postgres://... python scripts/audit_abandoned_keys.py --days 90 --revoke
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

import asyncpg


_QUERY = """
    SELECT k.id,
           k.key_prefix,
           k.name,
           k.created_at,
           k.last_used_at,
           u.email
    FROM api_key k
    JOIN app_user u ON k.user_id = u.id
    WHERE k.revoked_at IS NULL
      AND (
          (k.last_used_at IS NOT NULL
              AND k.last_used_at < NOW() - ($1 || ' days')::interval)
          OR
          (k.last_used_at IS NULL
              AND k.created_at < NOW() - ($1 || ' days')::interval)
      )
    ORDER BY COALESCE(k.last_used_at, k.created_at)
"""


async def _run_with_conn(conn, *, days: int, revoke: bool) -> int:
    rows = await conn.fetch(_QUERY, str(days))
    if not rows:
        print(f"no abandoned keys (>{days} days idle)")
        return 0

    print(f"abandoned keys (>{days} days idle): {len(rows)}")
    for r in rows:
        last = r["last_used_at"].isoformat() if r["last_used_at"] else "never"
        print(
            f"  {r['key_prefix']:>10}  user={r['email']:<32}  "
            f"name={r['name']!r:<25}  last_used={last}"
        )

    if revoke:
        reason = f"abandoned_{days}d"
        ids = [r["id"] for r in rows]
        await conn.execute(
            """UPDATE api_key
               SET revoked_at = NOW(), revoked_reason = $1
               WHERE id = ANY($2)""",
            reason,
            ids,
        )
        print(f"revoked {len(ids)} keys with reason={reason!r}")

    return len(rows)


async def audit(*, days: int, revoke: bool, conn=None) -> int:
    """Return the number of abandoned keys found (and optionally revoked).

    `conn` is for testability; when None, opens a fresh connection from
    DATABASE_URL.
    """
    if conn is not None:
        return await _run_with_conn(conn, days=days, revoke=revoke)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return -1

    own = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        return await _run_with_conn(own, days=days, revoke=revoke)
    finally:
        await own.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Idle threshold in days (default 180)",
    )
    parser.add_argument(
        "--revoke",
        action="store_true",
        help="Revoke abandoned keys in place. Default is alert-only.",
    )
    args = parser.parse_args()

    if args.days < 1:
        print("--days must be >= 1", file=sys.stderr)
        return 2

    rows = asyncio.run(audit(days=args.days, revoke=args.revoke))
    return 0 if rows >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
