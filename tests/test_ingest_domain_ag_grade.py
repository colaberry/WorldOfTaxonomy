"""Tests for Agriculture Commodity Grade domain taxonomy ingester.

RED tests - written before any implementation exists.

Commodity grade taxonomy organizes USDA quality grades into categories:
  Grain Grades   (dag_grain*)  - US No. 1-5 + sample grade for grains
  Livestock Grades (dag_live*) - USDA prime/choice/select + yield grades
  Produce Grades (dag_prod*)   - US Fancy, Extra No.1, No.1, No.2, No.3
  Dairy Grades   (dag_dairy*)  - Grade A, Grade B, Grade AA butter/cheese
  Egg Grades     (dag_egg*)    - Grade AA, Grade A, Grade B

Source: USDA Agricultural Marketing Service (AMS) grading standards. Public domain.
"""
import asyncio
import pytest

from world_of_taxanomy.ingest.domain_ag_grade import (
    GRADE_NODES,
    _determine_level,
    _determine_parent,
    ingest_domain_ag_grade,
)


class TestDetermineLevel:
    def test_grain_category_is_level_1(self):
        assert _determine_level("dag_grain") == 1

    def test_grain_grade_is_level_2(self):
        assert _determine_level("dag_grain_1") == 2

    def test_livestock_category_is_level_1(self):
        assert _determine_level("dag_live") == 1

    def test_livestock_grade_is_level_2(self):
        assert _determine_level("dag_live_prime") == 2


class TestDetermineParent:
    def test_grain_category_has_no_parent(self):
        assert _determine_parent("dag_grain") is None

    def test_grain_grade_parent_is_grain(self):
        assert _determine_parent("dag_grain_1") == "dag_grain"

    def test_livestock_grade_parent_is_live(self):
        assert _determine_parent("dag_live_prime") == "dag_live"


class TestGradeNodes:
    def test_nodes_list_is_non_empty(self):
        assert len(GRADE_NODES) > 0

    def test_has_grain_category(self):
        codes = [n[0] for n in GRADE_NODES]
        assert "dag_grain" in codes

    def test_has_livestock_category(self):
        codes = [n[0] for n in GRADE_NODES]
        assert "dag_live" in codes

    def test_has_produce_category(self):
        codes = [n[0] for n in GRADE_NODES]
        assert "dag_prod" in codes

    def test_has_us_no1_grain(self):
        codes = [n[0] for n in GRADE_NODES]
        assert "dag_grain_1" in codes

    def test_has_usda_prime(self):
        codes = [n[0] for n in GRADE_NODES]
        assert "dag_live_prime" in codes

    def test_all_titles_non_empty(self):
        for code, title, level, parent in GRADE_NODES:
            assert title.strip(), f"Empty title for '{code}'"

    def test_no_duplicate_codes(self):
        codes = [n[0] for n in GRADE_NODES]
        assert len(codes) == len(set(codes))

    def test_level_1_has_no_parent(self):
        for code, title, level, parent in GRADE_NODES:
            if level == 1:
                assert parent is None

    def test_level_2_has_parent(self):
        for code, title, level, parent in GRADE_NODES:
            if level == 2:
                assert parent is not None


def test_domain_ag_grade_module_importable():
    assert callable(ingest_domain_ag_grade)
    assert isinstance(GRADE_NODES, list)


def test_ingest_domain_ag_grade(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count = await ingest_domain_ag_grade(conn)
            assert count > 0
            row = await conn.fetchrow(
                "SELECT id, code_count FROM domain_taxonomy "
                "WHERE id = 'domain_ag_grade'"
            )
            assert row is not None
            assert row["code_count"] == count
    asyncio.get_event_loop().run_until_complete(_run())


def test_ingest_domain_ag_grade_idempotent(db_pool):
    async def _run():
        from world_of_taxanomy.ingest.naics import ingest_naics_2022
        async with db_pool.acquire() as conn:
            await ingest_naics_2022(conn)
            count1 = await ingest_domain_ag_grade(conn)
            count2 = await ingest_domain_ag_grade(conn)
            assert count1 == count2
    asyncio.get_event_loop().run_until_complete(_run())
