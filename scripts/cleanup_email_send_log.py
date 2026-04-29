"""Daily janitor for the `email_send_log` audit table.

The table is the backing store for the global email-send budget guard
(see `world_of_taxonomy.api.rate_guard.check_email_send_budget`). Only
the trailing hour matters for the guard, but rows are valuable for
abuse triage for ~7 days. Beyond that, they are dead weight that grows
~4 MB / week at the default 200/hour cap.

Schedule this script daily via Cloud Scheduler -> Cloud Run Job, or as
a local cron entry. Idempotent and safe to re-run.

Usage:
    DATABASE_URL=postgres://... python scripts/cleanup_email_send_log.py
    DATABASE_URL=postgres://... python scripts/cleanup_email_send_log.py --days 14
    DATABASE_URL=postgres://... python scripts/cleanup_email_send_log.py --dry-run

Exit code is 0 on success regardless of how many rows were deleted (so
a daily cron with no rows to clean does not page anyone). Non-zero
indicates a real DB error.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

import asyncpg


async def _run_with_conn(conn, *, days: int, dry_run: bool) -> int:
    if dry_run:
        count = await conn.fetchval(
            """SELECT count(*) FROM email_send_log
               WHERE sent_at < NOW() - ($1 || ' days')::interval""",
            str(days),
        )
        print(f"[dry-run] would delete {count} rows older than {days} days")
        return count or 0

    result = await conn.execute(
        """DELETE FROM email_send_log
           WHERE sent_at < NOW() - ($1 || ' days')::interval""",
        str(days),
    )
    try:
        deleted = int(result.split()[-1])
    except (IndexError, ValueError):
        deleted = 0
    print(f"deleted {deleted} rows older than {days} days")
    return deleted


async def cleanup(*, days: int, dry_run: bool, conn=None) -> int:
    """Delete email_send_log rows older than `days`.

    `conn` is for testability (so tests can pass a connection that has
    the right search_path configured). When None, opens a fresh
    connection from DATABASE_URL.
    """
    if conn is not None:
        return await _run_with_conn(conn, days=days, dry_run=dry_run)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return -1

    own = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        return await _run_with_conn(own, days=days, dry_run=dry_run)
    finally:
        await own.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Delete rows older than this many days (default 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be deleted without changing anything",
    )
    args = parser.parse_args()

    if args.days < 1:
        print("--days must be >= 1", file=sys.stderr)
        return 2

    rows = asyncio.run(cleanup(days=args.days, dry_run=args.dry_run))
    return 0 if rows >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
