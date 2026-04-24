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


class TestConfigManagerMeta:
    def _mgr(self, tmp_path: Path) -> "app.ConfigManager":
        return app.ConfigManager(base_dir=tmp_path / "Claude-3p")

    def test_ensure_meta_creates_file_if_missing(self, tmp_path):
        mgr = self._mgr(tmp_path)
        (tmp_path / "Claude-3p" / "configLibrary").mkdir(parents=True)
        mgr.ensure_meta()
        meta_path = tmp_path / "Claude-3p" / "configLibrary" / "_meta.json"
        assert meta_path.exists()
        assert json.loads(meta_path.read_text("utf-8")) == {
            "appliedId": None,
            "entries": [],
        }

    def test_ensure_meta_leaves_existing_file(self, tmp_path):
        mgr = self._mgr(tmp_path)
        lib = tmp_path / "Claude-3p" / "configLibrary"
        lib.mkdir(parents=True)
        meta_path = lib / "_meta.json"
        existing = {"appliedId": "abc", "entries": [{"id": "abc", "name": "X"}]}
        meta_path.write_text(json.dumps(existing), "utf-8")
        mgr.ensure_meta()
        assert json.loads(meta_path.read_text("utf-8")) == existing

    def test_read_meta_returns_parsed_dict(self, tmp_path):
        mgr = self._mgr(tmp_path)
        lib = tmp_path / "Claude-3p" / "configLibrary"
        lib.mkdir(parents=True)
        (lib / "_meta.json").write_text(
            json.dumps({"appliedId": "id1", "entries": []}), "utf-8"
        )
        assert mgr.read_meta() == {"appliedId": "id1", "entries": []}

    def test_save_meta_writes_utf8_json(self, tmp_path):
        mgr = self._mgr(tmp_path)
        lib = tmp_path / "Claude-3p" / "configLibrary"
        lib.mkdir(parents=True)
        data = {"appliedId": "中文id", "entries": [{"id": "中文id", "name": "档案"}]}
        mgr.save_meta(data)
        raw = (lib / "_meta.json").read_text("utf-8")
        assert json.loads(raw) == data

    def test_claude_dir_exists_false_when_missing(self, tmp_path):
        mgr = self._mgr(tmp_path)
        assert mgr.claude_dir_exists() is False

    def test_claude_dir_exists_true_when_present(self, tmp_path):
        mgr = self._mgr(tmp_path)
        (tmp_path / "Claude-3p").mkdir()
        assert mgr.claude_dir_exists() is True
