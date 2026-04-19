"""Tests for the public /api/v1/classify/demo endpoint (email-gated, no auth).

The demo endpoint is the web-facing classify surface. Anonymous users
provide an email in exchange for a classify query. The email goes into
the `classify_lead` table for lead nurture; results are limited to a
smaller surface than the authenticated /classify endpoint to preserve
the Pro-tier value proposition.
"""

import asyncio
import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestClassifyLeadSchema:
    """The classify_lead table must exist with the expected shape."""

    def test_classify_lead_table_exists(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                      AND table_name = 'classify_lead'
                    """
                )
                return row

        assert _run(go()) is not None

    def test_classify_lead_required_columns(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'classify_lead'
                    ORDER BY ordinal_position
                    """
                )
                return {r["column_name"]: (r["data_type"], r["is_nullable"]) for r in rows}

        cols = _run(go())
        assert "id" in cols
        assert "email" in cols and cols["email"][1] == "NO"
        assert "query_text" in cols and cols["query_text"][1] == "NO"
        assert "created_at" in cols

    def test_classify_lead_insert_and_retrieve(self, db_pool):
        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO classify_lead (email, query_text) VALUES ($1, $2)",
                    "test@example.com",
                    "telemedicine platform",
                )
                return await conn.fetchrow(
                    "SELECT email, query_text FROM classify_lead WHERE email = $1",
                    "test@example.com",
                )

        row = _run(go())
        assert row["email"] == "test@example.com"
        assert row["query_text"] == "telemedicine platform"


class TestClassifyDemoRequest:
    """Pydantic validation rules for the demo request body."""

    def test_email_is_required(self):
        from pydantic import ValidationError
        from world_of_taxonomy.api.routers.classify_demo import ClassifyDemoRequest

        with pytest.raises(ValidationError):
            ClassifyDemoRequest(text="software company")

    def test_text_min_length_enforced(self):
        from pydantic import ValidationError
        from world_of_taxonomy.api.routers.classify_demo import ClassifyDemoRequest

        with pytest.raises(ValidationError):
            ClassifyDemoRequest(email="user@example.com", text="x")

    def test_invalid_email_rejected(self):
        from pydantic import ValidationError
        from world_of_taxonomy.api.routers.classify_demo import ClassifyDemoRequest

        with pytest.raises(ValidationError):
            ClassifyDemoRequest(email="not-an-email", text="software company")

    def test_valid_request(self):
        from world_of_taxonomy.api.routers.classify_demo import ClassifyDemoRequest

        req = ClassifyDemoRequest(email="user@example.com", text="telemedicine platform")
        assert req.email == "user@example.com"
        assert req.text == "telemedicine platform"


class TestClassifyDemoHandler:
    """Direct handler call - captures lead + returns classify results."""

    def test_handler_persists_lead_and_returns_matches(self, db_pool):
        from world_of_taxonomy.api.routers.classify_demo import (
            ClassifyDemoRequest,
            classify_demo_handler,
        )

        req = ClassifyDemoRequest(email="lead@example.com", text="manufacturing")

        async def go():
            async with db_pool.acquire() as conn:
                result = await classify_demo_handler(
                    req,
                    conn=conn,
                    ip_address="127.0.0.1",
                    user_agent="pytest",
                    referrer=None,
                )
                lead_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM classify_lead WHERE email = $1",
                    "lead@example.com",
                )
                return result, lead_count

        result, lead_count = _run(go())
        assert lead_count == 1
        assert result["query"] == "manufacturing"
        assert "disclaimer" in result
        # Response is split into domain_matches + standard_matches; legacy
        # flat `matches` key is intentionally absent.
        assert "matches" not in result
        assert "domain_matches" in result
        assert "standard_matches" in result
        assert isinstance(result["domain_matches"], list)
        assert isinstance(result["standard_matches"], list)
        # Demo is capped to a limited surface
        assert result.get("demo") is True

    def test_handler_caps_systems_to_demo_set(self, db_pool):
        """Demo users get at most 5 systems regardless of input."""
        from world_of_taxonomy.api.routers.classify_demo import (
            ClassifyDemoRequest,
            classify_demo_handler,
        )

        req = ClassifyDemoRequest(email="lead2@example.com", text="farming")

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_demo_handler(
                    req,
                    conn=conn,
                    ip_address=None,
                    user_agent=None,
                    referrer=None,
                )

        result = _run(go())
        # Cap applies to the combined set across both categories.
        total = len(result["domain_matches"]) + len(result["standard_matches"])
        assert total <= 13  # 5 standards + up to 8 top domain systems

    def test_handler_caps_results_per_system(self, db_pool):
        """Demo users get at most 3 results per system (vs 20 on paid)."""
        from world_of_taxonomy.api.routers.classify_demo import (
            ClassifyDemoRequest,
            classify_demo_handler,
        )

        req = ClassifyDemoRequest(email="lead3@example.com", text="agriculture")

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_demo_handler(
                    req,
                    conn=conn,
                    ip_address=None,
                    user_agent=None,
                    referrer=None,
                )

        result = _run(go())
        for match in result["domain_matches"] + result["standard_matches"]:
            assert len(match["results"]) <= 3
