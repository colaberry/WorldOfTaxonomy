"""Tests for the UN M.49 description builder.

UN M.49 uses 3-digit numeric codes for:
- ``001`` World (level 0)
- 5 continents (level 1): 002 Africa, 009 Oceania, 019 Americas, 142 Asia, 150 Europe
- 24 sub-regions (level 2)
- 249 countries (level 3)

Country codes map 1:1 to ISO 3166-1 alpha-2 via the ``country-code``
column in ``data/iso3166_all.csv``. We reuse the existing ISO 3166-2
``render_country`` to produce consistent text across the two systems.

Region codes render as a short synthesized description listing the
countries they group.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.un_m49_descriptions import (
    build_m49_mapping,
    render_region,
)


_SAMPLE_CSV = dedent("""\
name,alpha-2,alpha-3,country-code,iso_3166-2,region,sub-region,intermediate-region,region-code,sub-region-code,intermediate-region-code
Afghanistan,AF,AFG,004,ISO 3166-2:AF,Asia,Southern Asia,"",142,034,""
Albania,AL,ALB,008,ISO 3166-2:AL,Europe,Southern Europe,"",150,039,""
Algeria,DZ,DZA,012,ISO 3166-2:DZ,Africa,Northern Africa,"",002,015,""
""")


def test_render_region_world():
    out = render_region(code="001", title="World", member_countries=[
        "Afghanistan", "Albania", "Algeria",
    ])
    assert "World" in out or "countries" in out
    assert "3" in out  # mentions count of member countries


def test_render_region_continent():
    out = render_region(
        code="142", title="Asia",
        member_countries=["Afghanistan"],
        parent_title=None,
    )
    assert "Asia" in out
    assert "region" in out.lower() or "continent" in out.lower()


def test_render_region_subregion_mentions_parent():
    out = render_region(
        code="039", title="Southern Europe",
        member_countries=["Albania"],
        parent_title="Europe",
    )
    assert "Europe" in out
    assert "Southern Europe" in out


def test_build_m49_mapping_includes_countries_from_csv(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    mapping = build_m49_mapping(f)
    # Countries keyed by 3-digit M.49 code
    assert "004" in mapping
    assert "008" in mapping
    assert "012" in mapping
    assert "Afghanistan" in mapping["004"]
    assert "Albania" in mapping["008"]


def test_build_m49_mapping_includes_world_and_continents(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    mapping = build_m49_mapping(f)
    # World + the continents that appear in the sample
    assert "001" in mapping
    assert "002" in mapping  # Africa
    assert "142" in mapping  # Asia
    assert "150" in mapping  # Europe


def test_build_m49_mapping_includes_subregions(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    mapping = build_m49_mapping(f)
    # Sub-regions appearing in sample
    assert "015" in mapping  # Northern Africa
    assert "034" in mapping  # Southern Asia
    assert "039" in mapping  # Southern Europe


def test_build_m49_mapping_no_em_dashes(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    mapping = build_m49_mapping(f)
    for code, desc in mapping.items():
        assert "\u2014" not in desc, f"em-dash in {code}: {desc}"
