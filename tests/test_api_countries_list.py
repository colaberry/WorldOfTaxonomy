"""Tests for GET /api/v1/countries (list endpoint for the dropdown).

The country profile (`/{code}`) and bulk stats (`/stats`) endpoints
already exist. This adds a lightweight list endpoint that returns
`{code, title, system_count}` per country, sorted alphabetically by
title, for use by the frontend country filter dropdown.
"""

import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxonomy.api.app import create_app


@pytest.fixture
def app(db_pool):
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _seed_country_links(pool):
    """Seed a minimal iso_3166_1 system + country_system_link fixture."""
    async with pool.acquire() as conn:
        await conn.execute("SET search_path TO test_wot")
        await conn.execute(
            """INSERT INTO classification_system (id, name, full_name, region)
               VALUES ('iso_3166_1', 'ISO 3166-1', 'Country codes', 'Global')
               ON CONFLICT (id) DO NOTHING"""
        )
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code, sector_code, is_leaf)
               VALUES ('iso_3166_1', $1, $2, 1, NULL, $1, true)
               ON CONFLICT DO NOTHING""",
            [("DE", "Germany"), ("US", "United States"), ("IN", "India"), ("ZZ", "Zed")],
        )
        await conn.executemany(
            """INSERT INTO country_system_link (country_code, system_id, relevance)
               VALUES ($1, $2, $3)
               ON CONFLICT DO NOTHING""",
            [
                ("DE", "naics_2022", "recommended"),
                ("DE", "isic_rev4", "recommended"),
                ("US", "naics_2022", "official"),
                ("US", "isic_rev4", "recommended"),
                ("IN", "isic_rev4", "recommended"),
            ],
        )


def test_list_countries_returns_code_title_count(client, db_pool):
    async def _test():
        await _seed_country_links(db_pool)
        resp = await client.get("/api/v1/countries")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3  # ZZ has no links, filtered out
        by_code = {c["code"]: c for c in data}
        assert by_code["DE"]["title"] == "Germany"
        assert by_code["DE"]["system_count"] >= 2
        assert by_code["US"]["system_count"] >= 2
        assert by_code["US"]["has_official"] is True
        assert by_code["DE"]["has_official"] is False
    _run(_test())


def test_list_countries_alphabetical_by_title(client, db_pool):
    async def _test():
        await _seed_country_links(db_pool)
        resp = await client.get("/api/v1/countries")
        titles = [c["title"] for c in resp.json()]
        assert titles == sorted(titles)
    _run(_test())


def test_list_countries_excludes_countries_with_no_links(client, db_pool):
    """ZZ is seeded in iso_3166_1 but has no country_system_link rows."""
    async def _test():
        await _seed_country_links(db_pool)
        codes = {c["code"] for c in (await client.get("/api/v1/countries")).json()}
        assert "ZZ" not in codes
    _run(_test())
