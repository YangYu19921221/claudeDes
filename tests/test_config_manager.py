"""Tests for ConfigManager and the module-level normalize_base_url helper."""

import json
from pathlib import Path

import pytest

import claude_3p_gui as app


class TestNormalizeBaseUrl:
    def test_adds_trailing_slash(self):
        assert app.normalize_base_url("https://x.com") == "https://x.com/"

    def test_keeps_single_trailing_slash(self):
        assert app.normalize_base_url("https://x.com/") == "https://x.com/"

    def test_collapses_multiple_trailing_slashes(self):
        assert app.normalize_base_url("https://x.com///") == "https://x.com/"

    def test_strips_v1_suffix(self):
        assert app.normalize_base_url("https://x.com/v1") == "https://x.com/"

    def test_strips_v1_with_trailing_slash(self):
        assert app.normalize_base_url("https://x.com/v1/") == "https://x.com/"

    def test_preserves_path_that_isnt_v1(self):
        assert app.normalize_base_url("https://x.com/api") == "https://x.com/api/"

    def test_http_scheme(self):
        assert app.normalize_base_url("http://154.12.51.83") == "http://154.12.51.83/"
