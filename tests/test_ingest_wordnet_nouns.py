"""Tests for WordNet noun hypernym tree ingester.

Source: NLTK's WordNet 3.1 corpus (Princeton WordNet).
The Princeton WordNet noun database contains ~82K synsets organized
into a hypernym tree rooted at entity.n.01.

For instance synsets (proper nouns like Aristotle.n.01), WordNet uses
instance_hypernyms instead of hypernyms; we treat both as valid parent
edges. Multi-hypernym synsets (~1.7% of nouns) keep the first listed
hypernym as the canonical hierarchy edge; alternative parents are noted
in the description.
"""
import pytest

from world_of_taxonomy.ingest.wordnet_nouns import (
    parse_wordnet_nouns,
    ingest_wordnet_nouns,
    ENTITY_ROOT,
)


def _wordnet_available() -> bool:
    try:
        from nltk.corpus import wordnet as wn  # noqa: F401
        # Trigger lazy load
        wn.synset("entity.n.01")
        return True
    except Exception:
        return False


HAS_DATA = _wordnet_available()


@pytest.mark.skipif(not HAS_DATA, reason="NLTK WordNet corpus not installed")
class TestParser:
    def test_parses_at_least_70k_synsets(self):
        nodes = parse_wordnet_nouns()
        # Verified count is ~82,115; floor at 70,000 (~85%)
        assert len(nodes) >= 70_000, f"Expected >=70K nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_wordnet_nouns()
        codes = [n[0] for n in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_wordnet_nouns()
        for code, title, _l, _p, _d in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes_in_titles_or_descriptions(self):
        nodes = parse_wordnet_nouns()
        for code, title, _l, _p, desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"
            if desc:
                assert "\u2014" not in desc, f"Em-dash in description of {code}"

    def test_entity_root_is_level_1(self):
        nodes = parse_wordnet_nouns()
        roots = [n for n in nodes if n[0] == ENTITY_ROOT]
        assert len(roots) == 1
        code, _t, level, parent, _d = roots[0]
        assert level == 1
        assert parent is None

    def test_parent_validity(self):
        nodes = parse_wordnet_nouns()
        codes = {n[0] for n in nodes}
        for code, _t, _l, parent, _d in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in node set"

    def test_codes_use_synset_naming(self):
        nodes = parse_wordnet_nouns()
        for code, _t, _l, _p, _d in nodes:
            # Synset names look like 'dog.n.01', 'entity.n.01', etc.
            assert ".n." in code, f"Code {code} missing noun POS marker"

    def test_descriptions_present_for_all(self):
        nodes = parse_wordnet_nouns()
        with_desc = sum(1 for n in nodes if n[4] and len(n[4]) > 0)
        coverage = with_desc / len(nodes) if nodes else 0
        # WordNet has a gloss for every synset
        assert coverage >= 0.99, f"Description coverage {coverage:.2%} below 99%"

    def test_specific_canonical_synsets_present(self):
        nodes = parse_wordnet_nouns()
        codes = {n[0] for n in nodes}
        for s in ("entity.n.01", "dog.n.01", "person.n.01", "physical_entity.n.01"):
            assert s in codes, f"Expected canonical synset {s} not found"
