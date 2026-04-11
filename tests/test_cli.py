"""Tests for the CLI (__main__.py).

Retroactive TDD - covering argument parsing and command dispatch
that should have been tested before implementation.

These are pure unit tests - no database needed.
"""

import pytest

from world_of_taxanomy.__main__ import build_parser


# Mark all tests in this module to skip the autouse db fixture
pytestmark = pytest.mark.cli


class TestCliParser:
    def setup_method(self):
        self.parser = build_parser()

    def test_no_args_returns_none_command(self):
        args = self.parser.parse_args([])
        assert args.command is None

    def test_init(self):
        args = self.parser.parse_args(["init"])
        assert args.command == "init"

    def test_reset(self):
        args = self.parser.parse_args(["reset"])
        assert args.command == "reset"

    def test_ingest_naics(self):
        args = self.parser.parse_args(["ingest", "naics"])
        assert args.command == "ingest"
        assert args.target == "naics"

    def test_ingest_isic(self):
        args = self.parser.parse_args(["ingest", "isic"])
        assert args.command == "ingest"
        assert args.target == "isic"

    def test_ingest_crosswalk(self):
        args = self.parser.parse_args(["ingest", "crosswalk"])
        assert args.command == "ingest"
        assert args.target == "crosswalk"

    def test_ingest_all(self):
        args = self.parser.parse_args(["ingest", "all"])
        assert args.command == "ingest"
        assert args.target == "all"

    def test_ingest_invalid_target(self):
        with pytest.raises(SystemExit):
            self.parser.parse_args(["ingest", "invalid"])

    def test_browse_system_only(self):
        args = self.parser.parse_args(["browse", "naics_2022"])
        assert args.command == "browse"
        assert args.system_id == "naics_2022"
        assert args.code is None

    def test_browse_system_and_code(self):
        args = self.parser.parse_args(["browse", "naics_2022", "62"])
        assert args.command == "browse"
        assert args.system_id == "naics_2022"
        assert args.code == "62"

    def test_search_basic(self):
        args = self.parser.parse_args(["search", "hospital"])
        assert args.command == "search"
        assert args.query == "hospital"
        assert args.system is None
        assert args.limit == 20

    def test_search_with_system(self):
        args = self.parser.parse_args(["search", "health", "--system", "naics_2022"])
        assert args.command == "search"
        assert args.query == "health"
        assert args.system == "naics_2022"

    def test_search_with_limit(self):
        args = self.parser.parse_args(["search", "farming", "--limit", "5"])
        assert args.command == "search"
        assert args.limit == 5

    def test_equiv_basic(self):
        args = self.parser.parse_args(["equiv", "naics_2022", "6211"])
        assert args.command == "equiv"
        assert args.system_id == "naics_2022"
        assert args.code == "6211"
        assert args.target is None

    def test_equiv_with_target(self):
        args = self.parser.parse_args(["equiv", "naics_2022", "6211", "--target", "isic_rev4"])
        assert args.command == "equiv"
        assert args.target == "isic_rev4"

    def test_stats(self):
        args = self.parser.parse_args(["stats"])
        assert args.command == "stats"

    def test_serve_defaults(self):
        args = self.parser.parse_args(["serve"])
        assert args.command == "serve"
        assert args.host == "0.0.0.0"
        assert args.port == 8000

    def test_serve_custom_port(self):
        args = self.parser.parse_args(["serve", "--port", "3000", "--host", "127.0.0.1"])
        assert args.command == "serve"
        assert args.host == "127.0.0.1"
        assert args.port == 3000
