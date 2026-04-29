"""Test fixtures for WorldOfTaxonomy.

Uses a real Neon PostgreSQL database but isolates tests in a separate
'test_wot' schema so production data in the 'public' schema is NEVER touched.

Uses synchronous wrappers around asyncpg to avoid Python 3.9 event loop issues.
"""

import asyncio
import os
import pytest
import asyncpg
from dotenv import load_dotenv
from pathlib import Path

# Load env
load_dotenv(Path(__file__).parent.parent / ".env")

TEST_SCHEMA = "test_wot"


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="session")
def database_url():
    """Get the test database URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


async def _set_test_search_path(conn):
    """Called every time a connection is acquired from the pool.

    Sets search_path to the test schema so all queries hit test_wot
    instead of public. This survives asyncpg's DISCARD ALL on release.
    """
    await conn.execute(f"SET search_path TO {TEST_SCHEMA}")


@pytest.fixture(scope="session")
def db_pool(database_url):
    """Create a connection pool for tests.

    Uses `setup` callback to set search_path on every acquire,
    ensuring queries always hit the test_wot schema (never public).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    pool = loop.run_until_complete(
        asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=1,
            setup=_set_test_search_path,
            statement_cache_size=0,  # Neon uses pgbouncer; no server-side prepared stmts
        )
    )
    yield pool
    # Drop the test schema entirely on session end
    loop.run_until_complete(_drop_test_schema(pool))
    loop.run_until_complete(pool.close())
    loop.close()


async def _drop_test_schema(pool):
    """Drop the test schema at end of session."""
    async with pool.acquire() as conn:
        await conn.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")


@pytest.fixture(autouse=True)
def setup_and_teardown(request):
    """Set up schema and seed data before each test, clean up after.

    Skips for tests marked with @pytest.mark.cli (pure unit tests, no DB needed).
    Also skips for tests that do not request db_pool in their own fixture list
    (e.g. unit tests testing pure _determine_level / _determine_parent helpers).
    All DB operations happen inside the test_wot schema - public is never touched.
    """
    if "cli" in [mark.name for mark in request.node.iter_markers()]:
        yield
        return
    # Only run DB setup when the test itself (or one of its fixtures) requests
    # db_pool. Pure unit-test functions/methods that don't take db_pool as a
    # parameter have no database dependency and should run without Neon.
    if "db_pool" not in request.fixturenames:
        yield
        return
    db_pool = request.getfixturevalue("db_pool")
    _run(_setup(db_pool))
    yield
    _run(_teardown(db_pool))


# Pre-seeded org id used by tests that insert app_user rows without
# caring about org bucketing. Phase 6+ tests should create their own
# orgs via the helpers in world_of_taxonomy/auth/orgs.py.
DEFAULT_TEST_ORG_ID = "00000000-0000-0000-0000-000000000001"


async def _setup(pool):
    schema_path = Path(__file__).parent.parent / "world_of_taxonomy" / "schema.sql"
    schema_sql = schema_path.read_text()

    devkeys_path = Path(__file__).parent.parent / "world_of_taxonomy" / "schema_devkeys.sql"
    devkeys_sql = devkeys_path.read_text() if devkeys_path.exists() else ""

    auth_schema_path = Path(__file__).parent.parent / "world_of_taxonomy" / "schema_auth.sql"
    auth_schema_sql = auth_schema_path.read_text() if auth_schema_path.exists() else ""

    async with pool.acquire() as conn:
        # Nuke and recreate the test schema from scratch - guarantees clean slate
        # This ONLY affects test_wot, NEVER public (where production data lives)
        await conn.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        await conn.execute(f"CREATE SCHEMA {TEST_SCHEMA}")
        await conn.execute(f"SET search_path TO {TEST_SCHEMA}")
        await conn.execute(schema_sql)
        # Dev-key system tables come before WoT-specific auth tables
        # because usage_log / daily_usage reference app_user / api_key.
        if devkeys_sql:
            await conn.execute(devkeys_sql)
        if auth_schema_sql:
            await conn.execute(auth_schema_sql)
        await _seed_default_org(conn)
        await seed_naics(conn)
        await seed_isic(conn)
        await seed_sic(conn)
        await seed_crosswalk(conn)
        await seed_country_system_links(conn)


async def _seed_default_org(conn):
    """Create one fixed-id corporate org so legacy auth tests can
    insert app_user rows without each having to manage bucketing."""
    await conn.execute(
        """INSERT INTO org (id, name, domain, kind)
           VALUES ($1::uuid, 'test_default', 'test.local', 'corporate')
           ON CONFLICT (id) DO NOTHING""",
        DEFAULT_TEST_ORG_ID,
    )


async def _teardown(pool):
    async with pool.acquire() as conn:
        await conn.execute(f"SET search_path TO {TEST_SCHEMA}")
        # Auth tables (may not exist yet)
        await conn.execute("DELETE FROM usage_log WHERE TRUE")
        await conn.execute("DELETE FROM email_send_log WHERE TRUE")
        await conn.execute("DELETE FROM magic_link_token WHERE TRUE")
        await conn.execute("DELETE FROM api_key WHERE TRUE")
        await conn.execute("DELETE FROM app_user WHERE TRUE")
        await conn.execute("DELETE FROM classify_lead WHERE TRUE")
        await conn.execute(
            "DELETE FROM org WHERE id != $1::uuid", DEFAULT_TEST_ORG_ID
        )
        # Core tables
        await conn.execute("DELETE FROM equivalence")
        await conn.execute("DELETE FROM classification_node")
        await conn.execute("DELETE FROM classification_system")


async def seed_naics(conn):
    await conn.execute("""
        INSERT INTO classification_system
            (id, name, full_name, region, version, authority, tint_color,
             source_url, data_provenance, license, source_file_hash)
        VALUES ('naics_2022', 'NAICS 2022',
                'North American Industry Classification System 2022',
                'North America', '2022', 'U.S. Census Bureau', '#F59E0B',
                'https://www.census.gov/naics/', 'official_download',
                'Public Domain (US Government)', 'abc123hash')
    """)
    naics_nodes = [
        ("11", "Agriculture, Forestry, Fishing and Hunting", None, 1, None, "11", False, 1),
        ("62", "Health Care and Social Assistance", None, 1, None, "62", False, 2),
        ("31-33", "Manufacturing", None, 1, None, "31-33", False, 3),
        ("111", "Crop Production", None, 2, "11", "11", False, 4),
        ("621", "Ambulatory Health Care Services", None, 2, "62", "62", False, 5),
        ("1111", "Oilseed and Grain Farming", None, 3, "111", "11", False, 6),
        ("6211", "Offices of Physicians", "Establishments with M.D. or D.O. degrees", 3, "621", "62", False, 7),
        ("11111", "Soybean Farming", None, 4, "1111", "11", False, 8),
        ("62111", "Offices of Physicians (except Mental Health)", None, 4, "6211", "62", True, 9),
        ("111110", "Soybean Farming", "Soybean farming and production", 5, "11111", "11", True, 10),
    ]
    for code, title, desc, level, parent, sector, leaf, seq in naics_nodes:
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, description, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('naics_2022', $1, $2, $3, $4, $5, $6, $7, $8)
        """, code, title, desc, level, parent, sector, leaf, seq)
    await conn.execute("UPDATE classification_system SET node_count = 10 WHERE id = 'naics_2022'")


async def seed_isic(conn):
    await conn.execute("""
        INSERT INTO classification_system (id, name, full_name, region, version, authority, tint_color)
        VALUES ('isic_rev4', 'ISIC Rev 4',
                'International Standard Industrial Classification Rev 4',
                'Global (UN)', 'Rev 4', 'United Nations Statistics Division', NULL)
    """)
    isic_nodes = [
        ("A", "Agriculture, forestry and fishing", None, 0, None, "A", False, 1),
        ("Q", "Human health and social work activities", None, 0, None, "Q", False, 2),
        ("01", "Crop and animal production", None, 1, "A", "A", False, 3),
        ("86", "Human health activities", None, 1, "Q", "Q", False, 4),
        ("011", "Growing of non-perennial crops", None, 2, "01", "A", False, 5),
        ("862", "Medical and dental practice activities", None, 2, "86", "Q", False, 6),
        ("0111", "Growing of cereals and other crops", None, 3, "011", "A", True, 7),
        ("8620", "Medical and dental practice activities", "General and specialist medical services", 3, "862", "Q", True, 8),
    ]
    for code, title, desc, level, parent, sector, leaf, seq in isic_nodes:
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, description, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('isic_rev4', $1, $2, $3, $4, $5, $6, $7, $8)
        """, code, title, desc, level, parent, sector, leaf, seq)
    await conn.execute("UPDATE classification_system SET node_count = 8 WHERE id = 'isic_rev4'")


async def seed_sic(conn):
    await conn.execute("""
        INSERT INTO classification_system (id, name, full_name, region, version, authority, tint_color)
        VALUES ('sic_1987', 'SIC 1987',
                'Standard Industrial Classification 1987',
                'USA/UK', '1987', 'U.S. Office of Management and Budget', '#78716C')
    """)
    sic_nodes = [
        ("A", "Agriculture, Forestry, And Fishing", None, 0, None, "A", False, 1),
        ("D", "Manufacturing", None, 0, None, "D", False, 2),
        ("01", "Agricultural Production Crops", None, 1, "A", "A", False, 3),
        ("20", "Food And Kindred Products", None, 1, "D", "D", False, 4),
        ("011", "Cash Grains", None, 2, "01", "A", False, 5),
        ("201", "Meat Products", None, 2, "20", "D", False, 6),
        ("0111", "Wheat", None, 3, "011", "A", True, 7),
        ("2011", "Meat Packing Plants", None, 3, "201", "D", True, 8),
    ]
    for code, title, desc, level, parent, sector, leaf, seq in sic_nodes:
        await conn.execute("""
            INSERT INTO classification_node
                (system_id, code, title, description, level, parent_code, sector_code, is_leaf, seq_order)
            VALUES ('sic_1987', $1, $2, $3, $4, $5, $6, $7, $8)
        """, code, title, desc, level, parent, sector, leaf, seq)
    await conn.execute("UPDATE classification_system SET node_count = 8 WHERE id = 'sic_1987'")


async def seed_country_system_links(conn):
    """Seed country_system_link for scope-resolution tests.

    Layout:
      US: naics_2022 (official), isic_rev4 (recommended), sic_1987 (historical)
      DE: isic_rev4 (recommended)
      CA: naics_2022 (regional), isic_rev4 (recommended)
    """
    links = [
        ("US", "naics_2022", "official"),
        ("US", "isic_rev4", "recommended"),
        ("US", "sic_1987", "historical"),
        ("DE", "isic_rev4", "recommended"),
        ("CA", "naics_2022", "regional"),
        ("CA", "isic_rev4", "recommended"),
    ]
    for country, system, relevance in links:
        await conn.execute(
            """INSERT INTO country_system_link (country_code, system_id, relevance)
               VALUES ($1, $2, $3)""",
            country, system, relevance,
        )


async def seed_crosswalk(conn):
    crosswalk = [
        ("naics_2022", "6211", "isic_rev4", "8620", "partial"),
        ("isic_rev4", "8620", "naics_2022", "6211", "partial"),
        ("naics_2022", "1111", "isic_rev4", "0111", "partial"),
        ("isic_rev4", "0111", "naics_2022", "1111", "partial"),
        ("naics_2022", "111110", "isic_rev4", "0111", "exact"),
        ("isic_rev4", "0111", "naics_2022", "111110", "exact"),  # reverse - seed must be symmetric
    ]
    for src_sys, src_code, tgt_sys, tgt_code, match in crosswalk:
        await conn.execute("""
            INSERT INTO equivalence (source_system, source_code, target_system, target_code, match_type)
            VALUES ($1, $2, $3, $4, $5)
        """, src_sys, src_code, tgt_sys, tgt_code, match)
