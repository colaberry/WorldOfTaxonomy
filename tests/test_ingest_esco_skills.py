"""Tests for ESCO Skills ingester.

RED tests - written before any implementation exists.

ESCO Skills are the competences/skills/knowledge nodes in the ESCO framework.
Published by the European Commission.
License: CC BY 4.0

ESCO has three types of skills:
  - skills (transversal skills, language skills, etc.)
  - knowledge
  - attitudes and values

All are stored as a flat system. The `skillType` column in the CSV
distinguishes them, but all are stored under system_id='esco_skills'.

Structure:
  ~13,890 skill nodes (v1.1.1)
  code = UUID extracted from conceptUri
  title = preferredLabel (English)
  level = 1 (all flat)
  parent_code = None
  sector_code = skill_type abbreviation ('S' for skill, 'K' for knowledge,
                'A' for attitude/value, '?' for unknown)
  is_leaf = True (all leaves)

Source: https://esco.ec.europa.eu/en/use-esco/download
"""
import asyncio
import os
import pytest

from world_of_taxanomy.ingest.esco_skills import (
    _extract_skill_code,
    _determine_skill_sector,
    ingest_esco_skills,
)

_DATA_PATH = "data/esco_skills_en.csv"


class TestExtractSkillCode:
    def test_extracts_uuid_from_skill_uri(self):
        uri = "http://data.europa.eu/esco/skill/b16c778c-6b4d-4c6e-a73f-9e1cf2ba1c3a"
        assert _extract_skill_code(uri) == "b16c778c-6b4d-4c6e-a73f-9e1cf2ba1c3a"

    def test_extracts_from_knowledge_uri(self):
        uri = "http://data.europa.eu/esco/skill/00000000-0000-0000-0000-000000000001"
        assert _extract_skill_code(uri) == "00000000-0000-0000-0000-000000000001"

    def test_trailing_slash_stripped(self):
        uri = "http://data.europa.eu/esco/skill/aaaa1111-2222-3333-4444-555566667777/"
        assert _extract_skill_code(uri) == "aaaa1111-2222-3333-4444-555566667777"

    def test_returns_non_empty_string(self):
        uri = "http://data.europa.eu/esco/skill/some-skill-code"
        result = _extract_skill_code(uri)
        assert result and result.strip()


class TestDetermineSkillSector:
    def test_skill_type_returns_s(self):
        assert _determine_skill_sector("skill/competence") == "S"

    def test_knowledge_type_returns_k(self):
        assert _determine_skill_sector("knowledge") == "K"

    def test_attitude_type_returns_a(self):
        assert _determine_skill_sector("attitude") == "A"

    def test_transversal_skill_returns_s(self):
        assert _determine_skill_sector("transversal skill") == "S"

    def test_unknown_type_returns_question_mark(self):
        assert _determine_skill_sector("") == "?"

    def test_case_insensitive(self):
        assert _determine_skill_sector("Knowledge") == "K"
        assert _determine_skill_sector("SKILL") == "S"


def test_esco_skills_module_importable():
    assert callable(ingest_esco_skills)
    assert callable(_extract_skill_code)
    assert callable(_determine_skill_sector)


@pytest.mark.skipif(
    not os.path.exists(_DATA_PATH),
    reason=f"ESCO skills CSV not found at {_DATA_PATH}. "
           "Run: python -m world_of_taxanomy ingest esco_skills",
)
def test_ingest_esco_skills_from_real_file(db_pool):
    """Integration test: ingest ESCO skills from downloaded CSV."""
    async def _run():
        async with db_pool.acquire() as conn:
            count = await ingest_esco_skills(conn, path=_DATA_PATH)
            assert count >= 13000, f"Expected >= 13000 ESCO skills, got {count}"
            assert count <= 16000, f"Expected <= 16000 ESCO skills, got {count}"

            row = await conn.fetchrow(
                "SELECT id, node_count FROM classification_system "
                "WHERE id = 'esco_skills'"
            )
            assert row is not None
            assert row["node_count"] == count

            # All nodes should be level=1, parent=None, is_leaf=True
            sample = await conn.fetchrow(
                "SELECT level, parent_code, is_leaf "
                "FROM classification_node "
                "WHERE system_id = 'esco_skills' "
                "LIMIT 1"
            )
            assert sample is not None
            assert sample["level"] == 1
            assert sample["parent_code"] is None
            assert sample["is_leaf"] is True

    asyncio.get_event_loop().run_until_complete(_run())


@pytest.mark.skipif(
    not os.path.exists(_DATA_PATH),
    reason=f"ESCO skills CSV not found at {_DATA_PATH}.",
)
def test_ingest_esco_skills_idempotent(db_pool):
    """Running ingest twice returns the same count both times."""
    async def _run():
        async with db_pool.acquire() as conn:
            count1 = await ingest_esco_skills(conn, path=_DATA_PATH)
            count2 = await ingest_esco_skills(conn, path=_DATA_PATH)
            assert count1 == count2

    asyncio.get_event_loop().run_until_complete(_run())
