"""Tests for per-code deep-link URL templates.

RED phase: classification_system must carry a `node_url_template`
column. NodeResponse must expose `source_url_for_code` derived by
interpolating `{code}` into that template. Systems with no template
return `None` (fallback to system-level source_url is a client concern).
"""

from __future__ import annotations

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxonomy.api.app import create_app
from world_of_taxonomy.query.provenance import (
    enrich_node_dict,
    get_system_provenance_map,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# -- Schema -----------------------------------------------------


def test_classification_system_has_node_url_template(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT column_name, is_nullable
                   FROM information_schema.columns
                   WHERE table_name = 'classification_system'
                     AND column_name = 'node_url_template'"""
            )
            assert row is not None, (
                "node_url_template column missing from classification_system"
            )
            assert row["is_nullable"] == "YES", (
                "node_url_template must be nullable; NULL means no per-code deep link"
            )
    _run(_test())


# -- Provenance query --------------------------------------------


def test_provenance_map_includes_node_url_template(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            await conn.execute(
                """UPDATE classification_system
                   SET node_url_template =
                         'https://www.census.gov/naics/?input={code}&year=2022'
                   WHERE id = 'naics_2022'"""
            )
            prov = await get_system_provenance_map(conn, ["naics_2022", "isic_rev4"])
            assert prov["naics_2022"]["node_url_template"] == (
                "https://www.census.gov/naics/?input={code}&year=2022"
            )
            assert prov["isic_rev4"]["node_url_template"] is None
    _run(_test())


# -- enrich_node_dict interpolation ------------------------------


def test_enrich_node_dict_interpolates_code():
    node = {"code": "11119", "system_id": "naics_2022"}
    prov = {
        "source_url": "https://www.census.gov/naics/",
        "node_url_template": "https://www.census.gov/naics/?input={code}&year=2022",
    }
    enrich_node_dict(node, prov)
    assert node["source_url_for_code"] == (
        "https://www.census.gov/naics/?input=11119&year=2022"
    )


def test_enrich_node_dict_without_template_returns_none():
    node = {"code": "0111", "system_id": "isic_rev4"}
    prov = {
        "source_url": "https://unstats.un.org/",
        "node_url_template": None,
    }
    enrich_node_dict(node, prov)
    assert node["source_url_for_code"] is None


def test_enrich_node_dict_hyphenated_code_interpolates():
    node = {"code": "31-33", "system_id": "naics_2022"}
    prov = {
        "source_url": "https://www.census.gov/naics/",
        "node_url_template": "https://www.census.gov/naics/?input={code}&year=2022",
    }
    enrich_node_dict(node, prov)
    assert node["source_url_for_code"] == (
        "https://www.census.gov/naics/?input=31-33&year=2022"
    )


# -- API contract ------------------------------------------------


@pytest.fixture
def app(db_pool):
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def test_node_response_includes_source_url_for_code(client, db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            await conn.execute(
                """UPDATE classification_system
                   SET node_url_template =
                         'https://www.census.gov/naics/?input={code}&year=2022'
                   WHERE id = 'naics_2022'"""
            )
        resp = await client.get("/api/v1/systems/naics_2022/nodes/6211")
        assert resp.status_code == 200
        data = resp.json()
        assert "source_url_for_code" in data
        assert data["source_url_for_code"] == (
            "https://www.census.gov/naics/?input=6211&year=2022"
        )
    _run(_test())


def test_node_response_source_url_for_code_null_without_template(client, db_pool):
    async def _test():
        # isic_rev4 seed has no template set
        resp = await client.get("/api/v1/systems/isic_rev4/nodes/8620")
        assert resp.status_code == 200
        data = resp.json()
        assert "source_url_for_code" in data
        assert data["source_url_for_code"] is None
    _run(_test())
