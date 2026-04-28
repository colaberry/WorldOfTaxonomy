"""Layer F: MCP server WOT_API_KEY startup gating.

Two requirements:
  - Without WOT_API_KEY or DATABASE_URL, main() exits non-zero with
    an actionable stderr message.
  - With WOT_API_KEY set, _wot_api_key() returns it; with it unset,
    None.

The full HTTP-mode pivot (each tool call dispatched over HTTP with
`Authorization: Bearer <key>`) is out of scope for PR #3; this PR
only adds the startup gate so an end-user installation of the PyPI
package fails loud rather than silent.
"""

import os
from unittest.mock import patch

import pytest


@pytest.mark.cli
class TestMcpCredentialGate:
    def test_main_exits_when_neither_var_is_set(self, capsys):
        from world_of_taxonomy.mcp import server
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as excinfo:
                server._check_credentials()
            assert excinfo.value.code == 2
        captured = capsys.readouterr()
        assert "WOT_API_KEY" in captured.err
        assert "DATABASE_URL" in captured.err
        assert "/developers" in captured.err

    def test_check_passes_with_api_key(self):
        from world_of_taxonomy.mcp import server
        with patch.dict(os.environ, {"WOT_API_KEY": "wot_dummy"}, clear=True):
            server._check_credentials()  # must not raise

    def test_check_passes_with_database_url(self):
        from world_of_taxonomy.mcp import server
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://x"}, clear=True):
            server._check_credentials()  # must not raise

    def test_wot_api_key_helper_returns_value_or_none(self):
        from world_of_taxonomy.mcp import server
        with patch.dict(os.environ, {"WOT_API_KEY": "wot_abcd"}, clear=True):
            assert server._wot_api_key() == "wot_abcd"
        with patch.dict(os.environ, {}, clear=True):
            assert server._wot_api_key() is None

    def test_wot_api_key_helper_strips_whitespace(self):
        from world_of_taxonomy.mcp import server
        with patch.dict(os.environ, {"WOT_API_KEY": "  wot_x  "}, clear=True):
            assert server._wot_api_key() == "wot_x"
        with patch.dict(os.environ, {"WOT_API_KEY": "   "}, clear=True):
            assert server._wot_api_key() is None
