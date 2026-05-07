"""Tests for FIBO (Financial Industry Business Ontology) ingester.

Source: https://github.com/edmcouncil/fibo (master branch zip)
The EDM Council publishes ~2,531 OWL classes across 7 modules covering
business entities, financial business and commerce, foundations,
securities, derivatives, indices, and loans.

Codes use module-prefixed local names (e.g., 'BE/SoleProprietor',
'SEC/Equity') to disambiguate the 13 cross-module local-name collisions.
"""
import os
import zipfile

import pytest

from world_of_taxonomy.ingest.fibo import (
    FIBO_MODULES,
    parse_fibo_zip,
    ingest_fibo,
)


DATA_FILE = "data/fibo-master.zip"
HAS_DATA = os.path.exists(DATA_FILE)


@pytest.mark.skipif(not HAS_DATA, reason="FIBO master zip not found")
class TestParser:
    def test_parses_at_least_2000_classes(self):
        nodes = parse_fibo_zip(DATA_FILE)
        # Verified count is ~2,531; floor at 2,000 (~80% of expected)
        assert len(nodes) >= 2000, f"Expected >=2000 nodes, got {len(nodes)}"

    def test_no_duplicate_codes(self):
        nodes = parse_fibo_zip(DATA_FILE)
        codes = [n[0] for n in nodes]
        assert len(codes) == len(set(codes)), "Duplicate codes found"

    def test_all_titles_non_empty(self):
        nodes = parse_fibo_zip(DATA_FILE)
        for code, title, _l, _p, _d in nodes:
            assert title and len(title) > 0, f"Empty title for {code}"

    def test_no_em_dashes_in_titles(self):
        nodes = parse_fibo_zip(DATA_FILE)
        for code, title, _l, _p, _desc in nodes:
            assert "\u2014" not in title, f"Em-dash in title of {code}"

    def test_codes_are_module_prefixed(self):
        nodes = parse_fibo_zip(DATA_FILE)
        valid_modules = set(FIBO_MODULES)
        for code, _t, _l, _p, _d in nodes:
            module = code.split("/", 1)[0]
            assert module in valid_modules, f"Unknown module prefix in {code}"

    def test_parent_validity(self):
        nodes = parse_fibo_zip(DATA_FILE)
        codes = {n[0] for n in nodes}
        for code, _t, _l, parent, _d in nodes:
            if parent is not None:
                assert parent in codes, f"{code} parent {parent} not in node set"

    def test_module_roots_exist(self):
        nodes = parse_fibo_zip(DATA_FILE)
        # Every module should have at least one level-1 root node
        roots_by_module = {}
        for code, _t, level, _p, _d in nodes:
            if level == 1:
                module = code.split("/", 1)[0]
                roots_by_module.setdefault(module, 0)
                roots_by_module[module] += 1
        for m in FIBO_MODULES:
            assert roots_by_module.get(m, 0) > 0, f"Module {m} has no level-1 root"

    def test_descriptions_present_for_most(self):
        nodes = parse_fibo_zip(DATA_FILE)
        with_desc = sum(1 for n in nodes if n[4] and len(n[4]) > 0)
        coverage = with_desc / len(nodes) if nodes else 0
        # FIBO has skos:definition on ~95% of classes
        assert coverage >= 0.90, f"Description coverage {coverage:.2%} below 90%"
