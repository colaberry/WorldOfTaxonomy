"""Database connection management for WorldOfTaxonomy.

Uses asyncpg for PostgreSQL with connection pooling.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import asyncpg
from dotenv import load_dotenv

from world_of_taxonomy.exceptions import DatabaseError

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

_logger = logging.getLogger(__name__)

# Connection pool singleton
_pool: Optional[asyncpg.Pool] = None

# Pool configuration. Env-overridable so operators can tune without
# redeploying code. command_timeout is applied to every query acquired
# from the pool, which is the main defence against runaway queries.
_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
_POOL_COMMAND_TIMEOUT = int(os.getenv("DB_COMMAND_TIMEOUT", "30"))

# Startup retry: Cloud SQL cold start (or any serverless Postgres
# provider's wake-from-idle) can take several seconds, long enough to
# lose a connection attempt. We retry with exponential backoff before
# giving up and surfacing the error.
_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "5"))
_CONNECT_BACKOFF_SECONDS = float(os.getenv("DB_CONNECT_BACKOFF_SECONDS", "1.0"))


def get_database_url() -> str:
    """Get the database URL from environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise DatabaseError(
            "DATABASE_URL environment variable is not set. "
            "Create a .env file with DATABASE_URL=postgresql://..."
        )
    return url


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool, with retry on cold-start."""
    global _pool
    if _pool is not None:
        return _pool

    last_exc: Optional[BaseException] = None
    for attempt in range(1, _CONNECT_RETRIES + 1):
        try:
            _pool = await asyncpg.create_pool(
                get_database_url(),
                min_size=_POOL_MIN_SIZE,
                max_size=_POOL_MAX_SIZE,
                command_timeout=_POOL_COMMAND_TIMEOUT,
            )
            if attempt > 1:
                _logger.info(
                    "DB pool connected on attempt %d/%d",
                    attempt,
                    _CONNECT_RETRIES,
                )
            return _pool
        except (OSError, asyncpg.PostgresError, asyncio.TimeoutError) as exc:
            last_exc = exc
            if attempt >= _CONNECT_RETRIES:
                break
            delay = _CONNECT_BACKOFF_SECONDS * (2 ** (attempt - 1))
            _logger.warning(
                "DB pool connect attempt %d/%d failed (%s); retrying in %.1fs",
                attempt,
                _CONNECT_RETRIES,
                exc.__class__.__name__,
                delay,
            )
            await asyncio.sleep(delay)

    raise DatabaseError(
        f"Failed to connect to database after {_CONNECT_RETRIES} attempts"
    ) from last_exc


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db():
    """Initialize the database schema."""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text()

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)


async def init_auth_db():
    """Initialize the auth database schema."""
    schema_path = Path(__file__).parent / "schema_auth.sql"
    schema_sql = schema_path.read_text()

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)


async def reset_db():
    """Drop all tables and recreate. Development only."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DROP TABLE IF EXISTS node_taxonomy_link CASCADE;
            DROP TABLE IF EXISTS domain_taxonomy CASCADE;
            DROP TABLE IF EXISTS equivalence CASCADE;
            DROP TABLE IF EXISTS classification_node CASCADE;
            DROP TABLE IF EXISTS classification_system CASCADE;
            DROP FUNCTION IF EXISTS update_search_vector CASCADE;
        """)
    await init_db()


def run_sync(coro):
    """Run an async function synchronously. For CLI usage."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an existing event loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)
