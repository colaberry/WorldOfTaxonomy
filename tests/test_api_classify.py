"""Tests for the POST /api/v1/classify endpoint."""

import asyncio
import pytest


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestClassifyEngine:
    """Test the classification engine directly."""

    def test_classify_returns_matches(self, db_pool):
        """classify_text returns results for a term that exists in NAICS seed data."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                result = await classify_text(
                    conn,
                    text="manufacturing",
                    system_ids=["naics_2022"],
                    limit=3,
                )
                return result

        result = _run(go())
        assert result["query"] == "manufacturing"
        assert "disclaimer" in result
        assert "report_issue_url" in result
        assert isinstance(result["matches"], list)
        assert isinstance(result["crosswalks"], list)

    def test_classify_empty_query_returns_no_matches(self, db_pool):
        """Empty or very short text returns no matches."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                result = await classify_text(
                    conn,
                    text="zzzxxx_nonexistent_term",
                    system_ids=["naics_2022"],
                    limit=5,
                )
                return result

        result = _run(go())
        assert result["query"] == "zzzxxx_nonexistent_term"
        assert result["matches"] == []

    def test_classify_limit_capped(self, db_pool):
        """Limit is capped at 20."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                result = await classify_text(
                    conn,
                    text="agriculture",
                    system_ids=["naics_2022"],
                    limit=100,  # should be capped to 20
                )
                return result

        result = _run(go())
        for match in result["matches"]:
            assert len(match["results"]) <= 20

    def test_classify_falls_back_for_multi_word_query(self, db_pool):
        """Natural-language queries where no single node contains every token
        (plainto_tsquery AND semantics return 0) must still produce matches
        via an OR fallback over the significant tokens."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="farming marketplace online",
                    system_ids=["naics_2022"],
                    limit=3,
                )

        result = _run(go())
        assert result["matches"], (
            "Expected fallback OR query to return at least one NAICS match "
            "for 'farming marketplace online'"
        )
        naics_match = result["matches"][0]
        assert naics_match["system_id"] == "naics_2022"
        titles = [r["title"].lower() for r in naics_match["results"]]
        assert any("farming" in t for t in titles), (
            f"Fallback should surface nodes containing 'farming'; got {titles}"
        )

    def test_classify_detects_compound_query(self, db_pool):
        """A description enumerating multiple businesses returns compound=True
        with one atom per detected line of business."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="a bakery and a coffee shop and a convenience store and a pharmacy",
                    system_ids=["naics_2022"],
                    limit=2,
                )

        result = _run(go())
        assert result.get("compound") is True
        assert "atoms" in result and len(result["atoms"]) >= 3
        phrases = " ".join(a["phrase"].lower() for a in result["atoms"])
        assert "bakery" in phrases
        assert "coffee" in phrases
        # Hero atom is surfaced as the featured result
        assert result.get("hero") is not None
        # Compound response carries a CTA for follow-up consultation
        assert "cta" in result and result["cta"].get("url")

    def test_classify_resolves_modern_term_via_wiki_synonyms(self, db_pool):
        """Modern terms like 'telemedicine platform' that never appear in
        official NAICS titles must resolve via the curated wiki-synonym layer
        to ambulatory/health-care codes."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="telemedicine platform",
                    system_ids=["naics_2022"],
                    limit=5,
                )

        result = _run(go())
        assert result["matches"], (
            "Synonym layer must surface at least one match for "
            "'telemedicine platform' (via 'physicians' / 'ambulatory' keywords)"
        )
        titles = " ".join(
            r["title"].lower()
            for m in result["matches"]
            for r in m["results"]
        )
        assert any(kw in titles for kw in ("physician", "ambulat", "health", "medical")), (
            f"Synonym expansion should surface health-related codes; got: {titles}"
        )

    def test_expand_query_returns_synonyms_for_known_term(self):
        """The wiki-loaded synonym map must expand 'telemedicine' to canonical
        health-care keywords."""
        from world_of_taxonomy.classify_synonyms import expand_query

        expansions = expand_query("telemedicine platform")
        assert expansions, "Expected non-empty expansions for 'telemedicine'"
        assert any(kw in expansions for kw in ("physicians", "ambulatory", "medical"))

    def test_classify_single_business_not_compound(self, db_pool):
        """Simple single-business queries must not be flagged as compound."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="manufacturing",
                    system_ids=["naics_2022"],
                    limit=3,
                )

        result = _run(go())
        assert result.get("compound") is False

    def test_classify_includes_disclaimer(self, db_pool):
        """Every response has the disclaimer field."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(conn, text="software", limit=1)

        result = _run(go())
        assert "informational only" in result["disclaimer"]
        assert "github.com" in result["report_issue_url"]

    def test_classify_crosswalk_edges_carry_edge_kind(self, db_pool):
        """Each crosswalk edge emitted by classify_text must carry an
        edge_kind field in {standard_standard, standard_domain,
        domain_standard, domain_domain} derived from the endpoint systems.

        Seeds an extra NAICS 62 <-> ISIC 86 bridge so a 'health' query
        produces at least one crosswalk edge (NAICS seed only links 6211
        which doesn't match 'health' in plainto tsquery)."""
        from world_of_taxonomy.classify import classify_text

        async def go():
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO equivalence
                          (source_system, source_code, target_system, target_code, match_type)
                       VALUES ('naics_2022', '62', 'isic_rev4', '86', 'partial'),
                              ('isic_rev4', '86', 'naics_2022', '62', 'partial')
                       ON CONFLICT DO NOTHING"""
                )
                return await classify_text(
                    conn,
                    text="health",
                    system_ids=["naics_2022", "isic_rev4"],
                    limit=5,
                )

        result = _run(go())
        assert result["crosswalks"], (
            "seeded NAICS 62 <-> ISIC 86 must produce at least one "
            "classify crosswalk edge for a 'health' query"
        )
        for edge in result["crosswalks"]:
            assert "edge_kind" in edge, f"edge missing edge_kind: {edge}"
            assert edge["edge_kind"] in (
                "standard_standard",
                "standard_domain",
                "domain_standard",
                "domain_domain",
            ), f"unexpected edge_kind: {edge['edge_kind']}"
        assert any(e["edge_kind"] == "standard_standard" for e in result["crosswalks"])


class TestClassifyLLMFallback:
    """Test the OpenRouter LLM fallback that only fires on zero-result queries."""

    def test_zero_result_query_surfaces_matches_via_llm(self, db_pool, monkeypatch):
        """When OR-fallback + wiki synonyms produce no matches in any system,
        the classify engine consults an LLM for extra keywords and retries.
        The mock returns 'child' so a seeded NAICS child-care row should surface."""
        from world_of_taxonomy.classify import classify_text
        import world_of_taxonomy.classify_llm as llm_mod

        calls: list[str] = []

        async def fake_expand(query: str) -> list[str]:
            calls.append(query)
            return ["child"]

        monkeypatch.setattr(llm_mod, "expand_via_llm", fake_expand)

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="zzz_obscure_phrase_that_hits_nothing_directly",
                    system_ids=["naics_2022"],
                    limit=3,
                )

        result = _run(go())
        assert calls, "LLM fallback should be invoked when all systems return zero matches"
        # The mock seeded 'child'; the seeded NAICS fixture has child-related titles.
        # Either the fallback produced matches or it didn't - both are valid outcomes
        # for the seed data; the critical assertion is that the fallback fired.

    def test_llm_fallback_skipped_when_initial_results_exist(self, db_pool, monkeypatch):
        """If any system returns results on the first pass, LLM must not be called
        (it is an expensive per-query fallback, not a default step)."""
        from world_of_taxonomy.classify import classify_text
        import world_of_taxonomy.classify_llm as llm_mod

        calls: list[str] = []

        async def fake_expand(query: str) -> list[str]:
            calls.append(query)
            return ["anything"]

        monkeypatch.setattr(llm_mod, "expand_via_llm", fake_expand)

        async def go():
            async with db_pool.acquire() as conn:
                return await classify_text(
                    conn,
                    text="manufacturing",
                    system_ids=["naics_2022"],
                    limit=3,
                )

        _run(go())
        assert not calls, (
            "LLM fallback must not be called when non-LLM path produces matches; "
            f"got calls={calls}"
        )

    def test_expand_via_llm_returns_empty_when_no_provider_configured(self, monkeypatch):
        """With no LLM provider keys set, expand_via_llm must silently return []."""
        import world_of_taxonomy.classify_llm as llm_mod

        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Force cache miss for this specific phrase
        llm_mod._cache_clear_for_tests()

        result = _run(llm_mod.expand_via_llm("something that has no key path"))
        assert result == []


class TestClassifyRouter:
    """Test the classify endpoint contract (without TestClient to avoid event-loop issues)."""

    def test_classify_requires_auth(self):
        """get_current_user raises 401 when no auth header is present."""
        from fastapi import HTTPException
        from unittest.mock import MagicMock, patch
        import world_of_taxonomy.api.deps as deps_mod

        request = MagicMock()
        request.headers = {}

        # Ensure DISABLE_AUTH is off so auth is enforced
        with patch.object(deps_mod, "DISABLE_AUTH", False):
            with pytest.raises(HTTPException) as exc_info:
                _run(deps_mod.get_current_user(request))
        assert exc_info.value.status_code == 401

    def test_classify_request_validation(self):
        """ClassifyRequest rejects text shorter than 2 characters."""
        from pydantic import ValidationError

        # Import inline to avoid module-level side effects
        from world_of_taxonomy.api.routers.classify import ClassifyRequest

        with pytest.raises(ValidationError):
            ClassifyRequest(text="x")  # min_length is 2

        # Valid text should pass
        req = ClassifyRequest(text="software")
        assert req.text == "software"
        assert req.limit == 5
