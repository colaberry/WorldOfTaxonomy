"""Database connection management for WorldOfTaxanomy.

Uses asyncpg for PostgreSQL with connection pooling.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import asyncpg
from dotenv import load_dotenv

from world_of_taxanomy.exceptions import DatabaseError

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

# Connection pool singleton
_pool: Optional[asyncpg.Pool] = None


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
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            get_database_url(),
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
    return _pool


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
