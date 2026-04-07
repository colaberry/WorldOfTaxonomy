"""Tests for hierarchy navigation queries."""

import asyncio
import pytest

from world_of_taxanomy.query.browse import (
    get_systems, get_system, get_roots, get_node, get_children,
    get_ancestors, get_subtree,
)
from world_of_taxanomy.exceptions import NodeNotFoundError, SystemNotFoundError


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_get_systems(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            systems = await get_systems(conn)
            assert len(systems) >= 2
            ids = {s.id for s in systems}
            assert "naics_2022" in ids
            assert "isic_rev4" in ids
    _run(_test())


def test_get_system(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            system = await get_system(conn, "naics_2022")
            assert system.name == "NAICS 2022"
            assert system.region == "North America"
            assert system.node_count == 10
    _run(_test())


def test_get_system_not_found(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            with pytest.raises(SystemNotFoundError):
                await get_system(conn, "nonexistent")
    _run(_test())


def test_get_roots(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            roots = await get_roots(conn, "naics_2022")
            assert len(roots) == 3
            codes = {r.code for r in roots}
            assert "11" in codes
            assert "62" in codes
            assert "31-33" in codes

            roots = await get_roots(conn, "isic_rev4")
            assert len(roots) == 2
            codes = {r.code for r in roots}
            assert "A" in codes
            assert "Q" in codes
    _run(_test())


def test_get_node(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            node = await get_node(conn, "naics_2022", "6211")
            assert node.title == "Offices of Physicians"
            assert node.level == 3
            assert node.parent_code == "621"
            assert node.sector_code == "62"
    _run(_test())


def test_get_node_not_found(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            with pytest.raises(NodeNotFoundError):
                await get_node(conn, "naics_2022", "99999")
    _run(_test())


def test_get_children(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            children = await get_children(conn, "naics_2022", "62")
            assert len(children) == 1
            assert children[0].code == "621"

            children = await get_children(conn, "naics_2022", "11")
            assert len(children) == 1
            assert children[0].code == "111"
    _run(_test())


def test_get_ancestors(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            ancestors = await get_ancestors(conn, "naics_2022", "111110")
            codes = [a.code for a in ancestors]
            assert codes == ["11", "111", "1111", "11111", "111110"]
    _run(_test())


def test_get_subtree(db_pool):
    async def _test():
        async with db_pool.acquire() as conn:
            tree = await get_subtree(conn, "naics_2022", "62")
            assert tree.code == "62"
            assert len(tree.children) == 1
            assert tree.children[0].code == "621"
            assert len(tree.children[0].children) == 1
            assert tree.children[0].children[0].code == "6211"
    _run(_test())
