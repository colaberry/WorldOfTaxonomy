"""Tests for the ISO 3166-2 description enricher.

The structural ingester persists country codes (e.g. ``AD``) at level 0
and subdivision codes (e.g. ``AD-02``) at level 1, with only the short
name as title. For descriptions we surface:

- On countries: the UN M.49 region + sub-region from ``iso3166_all.csv``
  plus the alpha-3 ISO code.
- On subdivisions: the subdivision type (Parish, State, Emirate, ...)
  and parent country name, sourced from ``pycountry``.
"""
from pathlib import Path
from textwrap import dedent

from world_of_taxonomy.ingest.iso3166_2_descriptions import (
    parse_iso3166_2_descriptions,
    render_country,
    render_subdivision,
)


_SAMPLE_CSV = dedent("""\
name,alpha-2,alpha-3,country-code,iso_3166-2,region,sub-region,intermediate-region,region-code,sub-region-code,intermediate-region-code
Andorra,AD,AND,020,ISO 3166-2:AD,Europe,Southern Europe,"",150,039,""
United States of America,US,USA,840,ISO 3166-2:US,Americas,Northern America,"",019,021,""
Antarctica,AQ,ATA,010,ISO 3166-2:AQ,"","","","","",""
""")


def test_render_country_with_region_and_subregion():
    meta = {
        "name": "Andorra",
        "alpha3": "AND",
        "region": "Europe",
        "sub_region": "Southern Europe",
    }
    out = render_country(meta)
    assert "Andorra" in out
    assert "Europe" in out
    assert "Southern Europe" in out
    assert "AND" in out


def test_render_country_without_region_still_renders_name_and_alpha3():
    meta = {"name": "Antarctica", "alpha3": "ATA", "region": "", "sub_region": ""}
    out = render_country(meta)
    assert "Antarctica" in out
    assert "ATA" in out
    # does not crash on empty region metadata
    assert out


def test_render_subdivision_formats_type_and_country():
    out = render_subdivision(code="AD-02", sub_type="Parish",
                             name="Canillo", country_name="Andorra")
    assert "Parish" in out
    assert "Andorra" in out
    assert "Canillo" in out


def test_render_subdivision_handles_district():
    out = render_subdivision(code="US-CA", sub_type="State",
                             name="California", country_name="United States")
    assert "State" in out
    assert "United States" in out


def test_render_subdivision_uses_an_before_vowel_type():
    out = render_subdivision(code="AE-AJ", sub_type="Emirate",
                             name="Ajman", country_name="United Arab Emirates")
    assert "is an Emirate" in out


def test_render_subdivision_uses_a_before_consonant_type():
    out = render_subdivision(code="AD-02", sub_type="Parish",
                             name="Canillo", country_name="Andorra")
    assert "is a Parish" in out


def test_parse_iso3166_2_descriptions_uses_csv_for_countries(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    out = parse_iso3166_2_descriptions(f)
    assert "AD" in out
    assert "US" in out
    assert "Europe" in out["AD"]
    assert "Northern America" in out["US"]


def test_parse_iso3166_2_descriptions_includes_subdivisions_from_pycountry(
    tmp_path: Path,
):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    out = parse_iso3166_2_descriptions(f)
    # pycountry knows Andorra's parishes
    assert "AD-02" in out
    assert "Andorra" in out["AD-02"]
    assert "Parish" in out["AD-02"]


def test_no_em_dash_in_any_rendered_value(tmp_path: Path):
    f = tmp_path / "iso3166.csv"
    f.write_text(_SAMPLE_CSV)
    out = parse_iso3166_2_descriptions(f)
    for v in out.values():
        assert "\u2014" not in v
