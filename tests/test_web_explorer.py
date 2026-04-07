"""Tests for the bubble explorer view.

TDD RED phase: the explorer is a single-page bubble drill-down
that uses the API to dynamically load children.
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxanomy.api.app import create_app


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
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def test_explorer_page_exists(client):
    async def _test():
        resp = await client.get("/explore")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
    _run(_test())


def test_explorer_has_canvas(client):
    async def _test():
        resp = await client.get("/explore")
        assert "explorer" in resp.text.lower() or "bubble" in resp.text.lower()
    _run(_test())


def test_explorer_loads_d3(client):
    async def _test():
        resp = await client.get("/explore")
        assert "d3" in resp.text
    _run(_test())


def test_explorer_loads_script(client):
    async def _test():
        resp = await client.get("/explore")
        assert "explorer.js" in resp.text
    _run(_test())


def test_explorer_js_served(client):
    async def _test():
        resp = await client.get("/static/js/explorer.js")
        assert resp.status_code == 200
        assert "javascript" in resp.headers.get("content-type", "")
    _run(_test())
