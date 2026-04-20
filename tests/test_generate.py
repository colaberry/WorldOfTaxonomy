"""Tests for AI taxonomy generation (magic wand).

Focuses on the contract: prompt shape, response parsing, and that the
per-suggestion `reason` field flows through end-to-end. All LLM calls are
mocked; we never reach a real provider.
"""
from __future__ import annotations

import asyncio
import json

import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def seeded_parent(db_pool):
    """Seed a minimal system + parent node for generate_children to read."""
    async def _seed():
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO classification_system (id, name, full_name, region, authority, node_count) "
                "VALUES ($1, $2, $3, $4, $5, $6) "
                "ON CONFLICT (id) DO NOTHING",
                "periodic_table",
                "Periodic Table",
                "Periodic Table (Element Groups)",
                "Global",
                "IUPAC",
                2,
            )
            await conn.execute(
                "INSERT INTO classification_node "
                "(system_id, code, title, description, level, parent_code, sector_code, is_leaf, seq_order) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                "ON CONFLICT (system_id, code) DO NOTHING",
                "periodic_table",
                "PT",
                "Element Groups",
                None,
                0,
                None,
                None,
                False,
                1,
            )
            await conn.execute(
                "INSERT INTO classification_node "
                "(system_id, code, title, description, level, parent_code, sector_code, is_leaf, seq_order) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                "ON CONFLICT (system_id, code) DO NOTHING",
                "periodic_table",
                "PT.01",
                "Alkali Metals",
                None,
                1,
                "PT",
                "PT",
                True,
                1,
            )

    _run(_seed())


class TestReasonField:
    def test_generate_children_preserves_reason_from_llm(self, monkeypatch, db_pool, seeded_parent):
        """The per-suggestion `reason` field from the LLM must flow into GeneratedNode."""
        from world_of_taxonomy.query import generate as gen_mod

        llm_reply = json.dumps([
            {
                "code": "PT.01.01",
                "title": "Lithium Group",
                "description": "Lithium and its isotopes.",
                "reason": "Lithium is the lightest alkali metal and commercially distinct.",
            },
            {
                "code": "PT.01.02",
                "title": "Sodium Group",
                "description": "Sodium and its compounds.",
                "reason": "Sodium is the most industrially produced alkali metal.",
            },
        ])

        async def fake_chat_json(*args, **kwargs):
            return llm_reply

        monkeypatch.setattr(gen_mod.llm_client, "chat_json", fake_chat_json)

        async def go():
            async with db_pool.acquire() as conn:
                return await gen_mod.generate_children(
                    conn, "periodic_table", "PT.01", count=2
                )

        results = _run(go())

        assert len(results) == 2
        assert results[0].code == "PT.01.01"
        assert results[0].reason == "Lithium is the lightest alkali metal and commercially distinct."
        assert results[1].reason == "Sodium is the most industrially produced alkali metal."

    def test_generate_children_tolerates_missing_reason(self, monkeypatch, db_pool, seeded_parent):
        """Older LLM replies without `reason` must not crash; reason defaults to None."""
        from world_of_taxonomy.query import generate as gen_mod

        llm_reply = json.dumps([
            {"code": "PT.01.01", "title": "Lithium Group"},
        ])

        async def fake_chat_json(*args, **kwargs):
            return llm_reply

        monkeypatch.setattr(gen_mod.llm_client, "chat_json", fake_chat_json)

        async def go():
            async with db_pool.acquire() as conn:
                return await gen_mod.generate_children(
                    conn, "periodic_table", "PT.01", count=1
                )

        results = _run(go())
        assert len(results) == 1
        assert results[0].reason is None


class TestPromptShape:
    def test_prompt_asks_for_reason_field(self):
        """The prompt must request `reason` in the JSON output so the LLM returns it."""
        from world_of_taxonomy.query.generate import _build_prompt

        ctx = {
            "system": {
                "id": "periodic_table",
                "name": "Periodic Table",
                "full_name": "Periodic Table",
                "region": "Global",
                "authority": "IUPAC",
            },
            "node": {
                "code": "PT.01",
                "title": "Alkali Metals",
                "description": None,
                "level": 1,
                "parent_code": "PT",
                "sector_code": "PT",
            },
            "ancestors": [{"code": "PT", "title": "Element Groups", "level": 0, "parent_code": None}],
            "children": [],
            "sibling_codes": ["PT.01", "PT.02"],
        }

        prompt = _build_prompt(ctx, count=5)

        assert "reason" in prompt.lower(), (
            "Prompt must instruct the LLM to include a `reason` for each suggestion"
        )


class TestGeneratedNodeSchema:
    def test_generated_node_has_optional_reason(self):
        from world_of_taxonomy.api.schemas import GeneratedNode

        node = GeneratedNode(code="X.1", title="Test", reason="because")
        assert node.reason == "because"

        node_no_reason = GeneratedNode(code="X.2", title="Test")
        assert node_no_reason.reason is None
