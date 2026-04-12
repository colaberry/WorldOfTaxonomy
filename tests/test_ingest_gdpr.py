"""Tests for GDPR Article Taxonomy ingester.

RED tests - written before any implementation exists.

GDPR = General Data Protection Regulation (EU) 2016/679.
Published by the European Union. Open (EUR-Lex). Hand-coded.
Reference: https://eur-lex.europa.eu/eli/reg/2016/679/oj

Hierarchy (2 levels):
  Chapter  (level 1, e.g. 'gdpr_ch_1')   - 11 chapters
  Article  (level 2, e.g. 'gdpr_art_1')  - 99 articles (leaves)

Codes: 'gdpr_ch_{N}' for chapters, 'gdpr_art_{N}' for articles.

Total: 11 chapters + 99 articles = 110 nodes.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.gdpr import (
    GDPR_NODES,
    _determine_level,
    _determine_parent,
    ingest_gdpr,
)


class TestDetermineLevel:
    def test_chapter_is_level_1(self):
        assert _determine_level("gdpr_ch_1") == 1

    def test_article_is_level_2(self):
        assert _determine_level("gdpr_art_1") == 2

    def test_chapter_11_is_level_1(self):
        assert _determine_level("gdpr_ch_11") == 1

    def test_article_99_is_level_2(self):
        assert _determine_level("gdpr_art_99") == 2


class TestDetermineParent:
    def test_chapter_has_no_parent(self):
        assert _determine_parent("gdpr_ch_1") is None

    def test_article_1_parent_is_ch_1(self):
        parent = _determine_parent("gdpr_art_1")
        assert parent is not None
        assert parent.startswith("gdpr_ch_")

    def test_article_99_has_parent(self):
        parent = _determine_parent("gdpr_art_99")
        assert parent is not None


class TestGdprNodes:
    def test_has_11_chapters(self):
        chapters = [n for n in GDPR_NODES if n[0].startswith("gdpr_ch_")]
        assert len(chapters) == 11

    def test_has_99_articles(self):
        articles = [n for n in GDPR_NODES if n[0].startswith("gdpr_art_")]
        assert len(articles) == 99

    def test_total_nodes_is_110(self):
        assert len(GDPR_NODES) == 110

    def test_all_titles_non_empty(self):
        for code, title, level, parent in GDPR_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in GDPR_NODES]
        assert len(codes) == len(set(codes))

    def test_chapters_have_no_parent(self):
        for code, title, level, parent in GDPR_NODES:
            if code.startswith("gdpr_ch_"):
                assert parent is None

    def test_articles_have_chapter_parent(self):
        for code, title, level, parent in GDPR_NODES:
            if code.startswith("gdpr_art_"):
                assert parent is not None
                assert parent.startswith("gdpr_ch_")


def test_gdpr_module_importable():
    assert callable(ingest_gdpr)
    assert isinstance(GDPR_NODES, list)


def test_ingest_gdpr(db_pool):
    """Integration test: ingest GDPR taxonomy."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_gdpr(conn)
            assert count == 110

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'gdpr_articles'"
            )
            assert row is not None
            assert row["node_count"] == 110

            # Chapter I should be level 1, no parent
            ch1 = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf FROM classification_node "
                "WHERE system_id = 'gdpr_articles' AND code = 'gdpr_ch_1'"
            )
            assert ch1["level"] == 1
            assert ch1["parent_code"] is None
            assert ch1["is_leaf"] is False

            # Article 5 should be level 2 and a leaf
            art5 = await conn.fetchrow(
                "SELECT level, is_leaf FROM classification_node "
                "WHERE system_id = 'gdpr_articles' AND code = 'gdpr_art_5'"
            )
            assert art5["level"] == 2
            assert art5["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_gdpr_idempotent(db_pool):
    """Running ingest twice returns 110 both times."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_gdpr(conn)
            count2 = await ingest_gdpr(conn)
            assert count1 == count2 == 110

    asyncio.get_event_loop().run_until_complete(_run())
