"""Tests for canary tokens + the /canary/{token} tripwire endpoint."""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from world_of_taxonomy.api.app import create_app
from world_of_taxonomy.canary import CANARY_HITS, CANARY_TOKENS, canary_block


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_canary_block_contains_all_tokens():
    block = canary_block()
    for tok in CANARY_TOKENS:
        assert tok in block


def test_llms_full_txt_embeds_canary_tokens():
    from world_of_taxonomy.wiki import build_llms_full_txt

    output = build_llms_full_txt()
    for tok in CANARY_TOKENS:
        assert tok in output


def test_canary_endpoint_known_token_counts(db_pool):
    async def _test():
        application = create_app()
        application.state.pool = db_pool
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as c:
            tok = CANARY_TOKENS[0]
            before = CANARY_HITS.labels(token=tok)._value.get()
            resp = await c.get(f"/canary/{tok}")
            assert resp.status_code == 200
            after = CANARY_HITS.labels(token=tok)._value.get()
            assert after == before + 1

    _run(_test())


def test_canary_endpoint_unknown_token_also_counts(db_pool):
    async def _test():
        application = create_app()
        application.state.pool = db_pool
        transport = ASGITransport(app=application)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as c:
            before = CANARY_HITS.labels(token="unknown")._value.get()
            resp = await c.get("/canary/made-up-token-xyz")
            assert resp.status_code == 200
            after = CANARY_HITS.labels(token="unknown")._value.get()
            assert after == before + 1

    _run(_test())
