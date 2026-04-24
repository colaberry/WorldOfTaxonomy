"""Tests for the ICD-11 MMS Simple Tabulation parser.

WHO publishes the Mortality and Morbidity Statistics (MMS) linearization
of ICD-11 as a tab-delimited ``SimpleTabulation-ICD-11-MMS-en.txt``
(also shipped as .xlsx). The columns include Code, Title, ClassKind,
ChapterNo, and CodingNote -- where CodingNote carries free-text
guidance such as "Use additional code if desired, to identify any
associated condition." We surface CodingNote into
``classification_node.description``; the file does not carry formal
<Definition> blocks (those live only in the WHO ICD-11 API).

Coverage is ~1.6% of codes (609 CodingNotes across 37K codes). Still
worth capturing -- the notes are the clinical-grade guidance that
coders actually reach for.
"""
from pathlib import Path

from world_of_taxonomy.ingest.icd11_descriptions import (
    parse_icd11_simple_tabulation,
)


# Fixture matches the exact column layout from WHO's file (20 columns,
# tab-delimited, UTF-8 with BOM, chapter header has no Code).
_HEADER = (
    "\ufeffFoundation URI\tLinearization URI\tCode\tBlockId\tTitle\t"
    "ClassKind\tDepthInKind\tIsResidual\tChapterNo\tBrowserLink\tisLeaf\t"
    "Primary tabulation\tGrouping1\tGrouping2\tGrouping3\tGrouping4\t"
    "Grouping5\tCodingNote\tParent\tVersion"
)

# Chapter row -- no Code, should be skipped.
_ROW_CHAPTER = (
    "http://id.who.int/icd/entity/1435254666\t"
    "http://id.who.int/icd/release/11/mms/1435254666\t\t\t"
    "\"Certain infectious or parasitic diseases\"\tchapter\t1\tFalse\t01\t"
    "browser\tFalse\t\t\t\t\t\t\t\t\t"
)

# Code row with a rich CodingNote.
_ROW_1D60 = (
    "http://id.who.int/icd/entity/111\t"
    "http://id.who.int/icd/release/11/mms/111\t1D60.03\t\t"
    "Some Ebola variant\tcategory\t3\tFalse\t01\tbrowser\tTrue\t\t"
    "\t\t\t\t\t"
    "This code should be used in conjunction with codes that identify "
    "the causative virus. Unusual manifestations include organ-specific syndromes."
    "\thttp://id.who.int/icd/entity/parent\t"
)

# Code row with a simpler "Use additional code" note.
_ROW_1C1G = (
    "http://id.who.int/icd/entity/222\t"
    "http://id.who.int/icd/release/11/mms/222\t1C1G\t\t"
    "Something\tcategory\t2\tFalse\t01\tbrowser\tFalse\t\t\t\t\t\t\t"
    "Use additional code if desired, to identify any associated condition."
    "\thttp://id.who.int/icd/entity/parent\t"
)

# Code row with no CodingNote -- should be omitted from the mapping.
_ROW_EH72 = (
    "http://id.who.int/icd/entity/333\t"
    "http://id.who.int/icd/release/11/mms/333\tEH72\t\t"
    "Drug-induced hair abnormalities\tcategory\t3\tFalse\t14\tbrowser\tTrue\t"
    "\t\t\t\t\t\t\thttp://id.who.int/icd/entity/parent\t"
)

# Code row with em-dashes in the CodingNote.
_ROW_EMDASH = (
    "http://id.who.int/icd/entity/444\t"
    "http://id.who.int/icd/release/11/mms/444\tXM1234\t\t"
    "Em\u2014dash thing\tcategory\t3\tFalse\t23\tbrowser\tTrue\t\t\t\t\t\t\t"
    "Note with em\u2014dash inside."
    "\thttp://id.who.int/icd/entity/parent\t"
)

_SAMPLE = "\n".join([_HEADER, _ROW_CHAPTER, _ROW_1D60, _ROW_1C1G, _ROW_EH72, _ROW_EMDASH])


def _write(path: Path, content: str = _SAMPLE) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_returns_mapping_keyed_by_code(tmp_path: Path):
    f = _write(tmp_path / "tab.txt")
    result = parse_icd11_simple_tabulation(f)
    assert "1D60.03" in result
    assert "1C1G" in result


def test_parse_skips_rows_without_code(tmp_path: Path):
    """Chapter/block rows without a Code column are not DB nodes."""
    f = _write(tmp_path / "tab.txt")
    result = parse_icd11_simple_tabulation(f)
    # Chapter row had no Code -- nothing to key on
    for v in result.values():
        assert "Certain infectious" not in v


def test_parse_skips_rows_without_coding_note(tmp_path: Path):
    """If a row has a code but no CodingNote, it is not emitted (nothing to say)."""
    f = _write(tmp_path / "tab.txt")
    result = parse_icd11_simple_tabulation(f)
    assert "EH72" not in result


def test_parse_emits_coding_note_as_labeled_block(tmp_path: Path):
    f = _write(tmp_path / "tab.txt")
    desc = parse_icd11_simple_tabulation(f)["1D60.03"]
    assert "**Coding note:**" in desc
    assert "causative virus" in desc


def test_parse_replaces_em_dash(tmp_path: Path):
    f = _write(tmp_path / "tab.txt")
    desc = parse_icd11_simple_tabulation(f)["XM1234"]
    assert "\u2014" not in desc
    assert "em-dash" in desc


def test_parse_accepts_zipped_archive(tmp_path: Path):
    """Parser should accept the WHO-style ZIP with the .txt inside."""
    import zipfile
    inner = _write(tmp_path / "SimpleTabulation-ICD-11-MMS-en.txt")
    zip_path = tmp_path / "SimpleTabulation-ICD-11-MMS-en.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(inner, arcname="SimpleTabulation-ICD-11-MMS-en.txt")
    result = parse_icd11_simple_tabulation(zip_path)
    assert "1D60.03" in result


def test_parse_strips_utf8_bom(tmp_path: Path):
    """The file starts with a UTF-8 BOM on the header; the parser must ignore it."""
    f = _write(tmp_path / "tab.txt")
    result = parse_icd11_simple_tabulation(f)
    # The BOM was on 'Foundation URI' -- if it leaked, the column index would
    # shift and we would get empty results.
    assert len(result) > 0
