"""Tests for wiki API endpoints.

TDD RED phase: verifies GET /api/v1/wiki and GET /api/v1/wiki/{slug}.
"""
from __future__ import annotations

import asyncio
import json

import pytest
from httpx import AsyncClient, ASGITransport

from world_of_taxonomy.api.app import create_app


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def app(db_pool):
    application = create_app()
    application.state.pool = db_pool
    return application


@pytest.fixture
def client(app):
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestWikiAPI:
    def test_list_wiki_pages(self, client):
        async def _test():
            resp = await client.get("/api/v1/wiki")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 11  # 10 content pages + architecture

        _run(_test())

    def test_list_wiki_pages_has_fields(self, client):
        async def _test():
            resp = await client.get("/api/v1/wiki")
            assert resp.status_code == 200
            data = resp.json()
            for entry in data:
                assert "slug" in entry
                assert "title" in entry
                assert "description" in entry

        _run(_test())

    def test_get_wiki_page(self, client):
        async def _test():
            resp = await client.get("/api/v1/wiki/getting-started")
            assert resp.status_code == 200
            data = resp.json()
            assert "content_markdown" in data
            assert len(data["content_markdown"]) > 100

        _run(_test())

    def test_get_wiki_page_has_fields(self, client):
        async def _test():
            resp = await client.get("/api/v1/wiki/getting-started")
            assert resp.status_code == 200
            data = resp.json()
            assert "slug" in data
            assert "title" in data
            assert "content_markdown" in data

        _run(_test())

    def test_get_wiki_page_not_found(self, client):
        async def _test():
            resp = await client.get("/api/v1/wiki/nonexistent-page")
            assert resp.status_code == 404

        _run(_test())
