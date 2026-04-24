# Claude-3p Windows GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a single-file Python tkinter GUI (`Claude3pSetup.exe`) that lets users pick one of 3 hardcoded gateway URLs, fetch models with their API key, and write Claude Desktop's Claude-3p config — mirroring the existing PS1 script but with fixed URLs only.

**Architecture:** One Python source file (`claude_3p_gui.py`) with three decoupled classes: `ConfigManager` (filesystem layer, pure), `ModelFetcher` (HTTP layer, pure), `App(tk.Tk)` (GUI layer). Pure layers are unit-tested with pytest; GUI is verified manually per the spec's acceptance checklist. PyInstaller `--onefile --windowed` packages to a single exe on Windows.

**Tech Stack:** Python 3.10+, tkinter (stdlib), urllib.request (stdlib), threading+queue (stdlib), pytest (dev only), PyInstaller (build only).

**Spec:** `docs/superpowers/specs/2026-04-24-claude-3p-gui-design.md`

---

## File Structure

```
Claude3pSetupWin/
├── claude_3p_gui.py           # Main source (~450 lines, all classes)
├── tests/
│   ├── __init__.py
│   ├── test_config_manager.py # pytest — ConfigManager
│   └── test_model_fetcher.py  # pytest — ModelFetcher (urlopen mocked)
├── build.bat                  # Windows build script
├── requirements-build.txt     # pyinstaller
├── requirements-dev.txt       # pytest
├── README.md                  # Build + usage instructions
├── .gitignore
└── docs/superpowers/
    ├── specs/2026-04-24-claude-3p-gui-design.md
    └── plans/2026-04-24-claude-3p-gui.md  (this file)
```

**Decomposition rationale**: one source file is appropriate here — the app is small (~450 lines) and the three classes have clean internal boundaries without needing separate modules. Separating into packages would add import ceremony without aiding comprehension. Tests live in `tests/` to keep the main file shippable as-is via PyInstaller.

**Note on testing**: Spec §8 says "no automated tests" specifically about GUI behavior. This plan adds lightweight pytest coverage for the two pure-logic classes (`ConfigManager`, `ModelFetcher`) since they have cheap-to-test edge cases (URL normalization, meta-json merging, HTTP endpoint fallback). GUI layer (`App`) remains manually verified.

---

## Task 1: Project scaffold

**Files:**
- Create: `/Users/apple/Desktop/Claude3pSetupWin/.gitignore`
- Create: `/Users/apple/Desktop/Claude3pSetupWin/requirements-build.txt`
- Create: `/Users/apple/Desktop/Claude3pSetupWin/requirements-dev.txt`
- Create: `/Users/apple/Desktop/Claude3pSetupWin/tests/__init__.py`
- Create: `/Users/apple/Desktop/Claude3pSetupWin/claude_3p_gui.py` (skeleton)

- [ ] **Step 1: Write `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.venv/
venv/

# PyInstaller
build/
dist/
*.spec

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Write `requirements-build.txt`**

```
pyinstaller>=6.0
```

- [ ] **Step 3: Write `requirements-dev.txt`**

```
pytest>=8.0
```

- [ ] **Step 4: Create empty `tests/__init__.py`** (empty file)

- [ ] **Step 5: Write `claude_3p_gui.py` skeleton**

```python
"""Claude Desktop 第三方网关配置 GUI.

Packaged to a single Windows .exe via PyInstaller. Mirrors claude-3p-setup.ps1
but restricts gateway URL to a hardcoded allowlist.
"""

import json
import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

GATEWAYS = [
    "https://pikachu.claudecode.love",
    "https://dk.claudecode.love",
    "http://154.12.51.83",
]

FETCH_TIMEOUT_SEC = 15


def normalize_base_url(url: str) -> str:
    """Strip trailing slash, strip /v1 suffix, then re-append /."""
    url = url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    return url + "/"


class ConfigManager:
    pass


class ModelFetcher:
    pass


class App(tk.Tk):
    pass


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify it imports cleanly**

Run: `cd /Users/apple/Desktop/Claude3pSetupWin && python3 -c "import claude_3p_gui; print('OK')"`

Expected output: `OK`

- [ ] **Step 7: Commit**

```bash
cd /Users/apple/Desktop/Claude3pSetupWin
git add .gitignore requirements-build.txt requirements-dev.txt tests/__init__.py claude_3p_gui.py
git commit -m "scaffold: project structure and skeleton"
```

---

## Task 2: `normalize_base_url` + pytest baseline

**Files:**
- Create: `tests/test_config_manager.py`
- Modify: `claude_3p_gui.py` (already has `normalize_base_url`, we just test it)

- [ ] **Step 1: Write failing tests**

Create `/Users/apple/Desktop/Claude3pSetupWin/tests/test_config_manager.py`:

```python
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
```

- [ ] **Step 2: Run tests, verify they pass** (this helper is already implemented in Task 1)

Run: `cd /Users/apple/Desktop/Claude3pSetupWin && python3 -m pytest tests/test_config_manager.py -v`

Expected: 7 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_config_manager.py
git commit -m "test: normalize_base_url"
```

---

## Task 3: `ConfigManager` meta-json operations

**Goal:** `ConfigManager` constructor takes a `base_dir: Path` (overridable for tests, defaults to `%APPDATA%\Claude-3p`). Implement `ensure_meta()`, `read_meta()`, `save_meta()`.

**Files:**
- Modify: `claude_3p_gui.py` (fill in `ConfigManager`)
- Modify: `tests/test_config_manager.py` (append tests)

- [ ] **Step 1: Append failing tests to `tests/test_config_manager.py`**

```python
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
```

- [ ] **Step 2: Run to confirm failure**

Run: `cd /Users/apple/Desktop/Claude3pSetupWin && python3 -m pytest tests/test_config_manager.py::TestConfigManagerMeta -v`

Expected: all tests fail with `AttributeError` on ConfigManager methods.

- [ ] **Step 3: Implement `ConfigManager` meta methods in `claude_3p_gui.py`**

Replace `class ConfigManager: pass` with:

```python
class ConfigManager:
    """Filesystem layer for Claude-3p configLibrary.

    All operations relative to `base_dir` (default %APPDATA%/Claude-3p).
    Constructor argument lets tests inject a tmp dir.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
            base_dir = Path(appdata) / "Claude-3p"
        self.base_dir = Path(base_dir)
        self.lib_dir = self.base_dir / "configLibrary"
        self.meta_path = self.lib_dir / "_meta.json"

    def claude_dir_exists(self) -> bool:
        return self.base_dir.exists()

    def ensure_meta(self) -> None:
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        if not self.meta_path.exists():
            self.save_meta({"appliedId": None, "entries": []})

    def read_meta(self) -> dict:
        return json.loads(self.meta_path.read_text("utf-8"))

    def save_meta(self, meta: dict) -> None:
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd /Users/apple/Desktop/Claude3pSetupWin && python3 -m pytest tests/test_config_manager.py -v`

Expected: all tests pass (7 from Task 2 + 6 from this task = 13 passed).

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py tests/test_config_manager.py
git commit -m "feat: ConfigManager meta-json operations"
```

---

## Task 4: `ConfigManager.write_profile`

**Goal:** Write a profile JSON to `configLibrary/{id}.json` and update `_meta.json`. Reuse profile_id if name matches existing entry (matches PS1 behavior).

**Files:**
- Modify: `claude_3p_gui.py` (extend `ConfigManager`)
- Modify: `tests/test_config_manager.py` (append tests)

- [ ] **Step 1: Append tests**

```python
class TestWriteProfile:
    def _mgr(self, tmp_path: Path) -> "app.ConfigManager":
        m = app.ConfigManager(base_dir=tmp_path / "Claude-3p")
        (tmp_path / "Claude-3p").mkdir()
        m.ensure_meta()
        return m

    def test_creates_new_profile_with_uuid(self, tmp_path):
        mgr = self._mgr(tmp_path)
        pid = mgr.write_profile(
            name="Default",
            base_url="https://dk.claudecode.love/",
            api_key="sk-test",
            models=["claude-opus-4-7", "claude-sonnet-4-6"],
        )
        assert isinstance(pid, str) and len(pid) == 36  # uuid4 length
        profile_file = mgr.lib_dir / f"{pid}.json"
        data = json.loads(profile_file.read_text("utf-8"))
        assert data == {
            "inferenceProvider": "gateway",
            "inferenceGatewayBaseUrl": "https://dk.claudecode.love/",
            "inferenceGatewayApiKey": "sk-test",
            "inferenceModels": ["claude-opus-4-7", "claude-sonnet-4-6"],
        }

    def test_updates_meta_applied_id_and_entries(self, tmp_path):
        mgr = self._mgr(tmp_path)
        pid = mgr.write_profile(
            name="MyProfile",
            base_url="https://dk.claudecode.love/",
            api_key="sk-test",
            models=["claude-opus-4-7"],
        )
        meta = mgr.read_meta()
        assert meta["appliedId"] == pid
        assert meta["entries"] == [{"id": pid, "name": "MyProfile"}]

    def test_reuses_id_when_name_matches_existing(self, tmp_path):
        mgr = self._mgr(tmp_path)
        pid1 = mgr.write_profile(
            name="Shared",
            base_url="https://dk.claudecode.love/",
            api_key="sk-1",
            models=["m1"],
        )
        pid2 = mgr.write_profile(
            name="Shared",
            base_url="https://pikachu.claudecode.love/",
            api_key="sk-2",
            models=["m2"],
        )
        assert pid1 == pid2
        # File is overwritten with new content
        data = json.loads((mgr.lib_dir / f"{pid2}.json").read_text("utf-8"))
        assert data["inferenceGatewayApiKey"] == "sk-2"
        assert data["inferenceModels"] == ["m2"]
        # Meta only has one entry
        meta = mgr.read_meta()
        assert len(meta["entries"]) == 1
        assert meta["entries"][0]["name"] == "Shared"

    def test_distinct_names_create_distinct_ids(self, tmp_path):
        mgr = self._mgr(tmp_path)
        pid1 = mgr.write_profile("A", "https://dk.claudecode.love/", "k", ["m"])
        pid2 = mgr.write_profile("B", "https://dk.claudecode.love/", "k", ["m"])
        assert pid1 != pid2
        meta = mgr.read_meta()
        assert meta["appliedId"] == pid2
        names = {e["name"] for e in meta["entries"]}
        assert names == {"A", "B"}
```

- [ ] **Step 2: Confirm failure**

Run: `python3 -m pytest tests/test_config_manager.py::TestWriteProfile -v`

Expected: failures on `write_profile` attribute.

- [ ] **Step 3: Implement `write_profile`**

Append to `ConfigManager`:

```python
    def write_profile(
        self,
        name: str,
        base_url: str,
        api_key: str,
        models: list[str],
    ) -> str:
        """Write profile JSON and update _meta.json. Returns profile id.

        Reuses existing id when a profile with the same name already exists.
        """
        self.ensure_meta()
        meta = self.read_meta()
        existing = next((e for e in meta["entries"] if e["name"] == name), None)
        profile_id = existing["id"] if existing else str(uuid.uuid4())

        profile = {
            "inferenceProvider": "gateway",
            "inferenceGatewayBaseUrl": base_url,
            "inferenceGatewayApiKey": api_key,
            "inferenceModels": list(models),
        }
        (self.lib_dir / f"{profile_id}.json").write_text(
            json.dumps(profile, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        meta["appliedId"] = profile_id
        if not existing:
            meta["entries"].append({"id": profile_id, "name": name})
        self.save_meta(meta)
        return profile_id
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_config_manager.py -v`

Expected: all tests pass (13 prior + 4 new = 17 passed).

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py tests/test_config_manager.py
git commit -m "feat: ConfigManager.write_profile with id reuse by name"
```

---

## Task 5: `ConfigManager.backup_library` and `restart_claude`

**Files:**
- Modify: `claude_3p_gui.py` (extend `ConfigManager`)
- Modify: `tests/test_config_manager.py` (append tests for backup — not restart)

- [ ] **Step 1: Append backup tests**

```python
class TestBackup:
    def test_backup_copies_library_to_timestamped_dir(self, tmp_path, monkeypatch):
        mgr = app.ConfigManager(base_dir=tmp_path / "Claude-3p")
        (tmp_path / "Claude-3p").mkdir()
        mgr.ensure_meta()
        mgr.write_profile("X", "https://dk.claudecode.love/", "k", ["m"])

        fixed_ts = "20260424-120000"
        monkeypatch.setattr(
            app, "_timestamp", lambda: fixed_ts, raising=False
        )

        backup_path = mgr.backup_library()

        assert backup_path.name == f"configLibrary.bak-{fixed_ts}"
        assert backup_path.is_dir()
        assert (backup_path / "_meta.json").exists()
        # Original still intact
        assert mgr.lib_dir.exists()

    def test_backup_noop_when_library_missing(self, tmp_path):
        mgr = app.ConfigManager(base_dir=tmp_path / "Claude-3p")
        # lib_dir does not exist
        assert mgr.backup_library() is None
```

- [ ] **Step 2: Confirm failure**

Run: `python3 -m pytest tests/test_config_manager.py::TestBackup -v`

Expected: `AttributeError: ... 'backup_library'`.

- [ ] **Step 3: Add `_timestamp` helper + implement `backup_library` and `restart_claude`**

In `claude_3p_gui.py`, **add a module-level helper below `normalize_base_url`**:

```python
def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")
```

Append to `ConfigManager`:

```python
    def backup_library(self) -> Path | None:
        """Copy configLibrary to a timestamped sibling dir. Returns new path or None."""
        if not self.lib_dir.exists():
            return None
        dest = self.base_dir / f"configLibrary.bak-{_timestamp()}"
        shutil.copytree(self.lib_dir, dest)
        return dest

    def restart_claude(self) -> bool:
        """Kill Claude.exe and start it again. Returns True on success, False if exe not found."""
        subprocess.run(
            ["taskkill", "/F", "/IM", "Claude.exe"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        candidates: list[Path] = []
        for root in (
            os.environ.get("LOCALAPPDATA"),
            os.environ.get("PROGRAMFILES"),
        ):
            if not root:
                continue
            claude_dir = Path(root) / "Claude"
            if claude_dir.exists():
                candidates.extend(claude_dir.glob("*.exe"))
        # Prefer Claude.exe explicitly if present
        exe = next((p for p in candidates if p.name.lower() == "claude.exe"), None)
        if exe is None and candidates:
            exe = candidates[0]
        if exe is None:
            return False
        subprocess.Popen([str(exe)], close_fds=True)
        return True
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_config_manager.py -v`

Expected: 19 passed (17 prior + 2 backup).

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py tests/test_config_manager.py
git commit -m "feat: ConfigManager backup_library and restart_claude"
```

---

## Task 6: `ModelFetcher`

**Goal:** Try `{base}v1/models` then `{base}models`, with headers `Authorization`, `x-api-key`, `anthropic-version`. Return sorted unique model ids, or raise on failure.

**Files:**
- Modify: `claude_3p_gui.py` (fill in `ModelFetcher`)
- Create: `tests/test_model_fetcher.py`

- [ ] **Step 1: Write tests**

Create `tests/test_model_fetcher.py`:

```python
"""Tests for ModelFetcher (urllib mocked)."""

import io
import json
from unittest.mock import patch, MagicMock

import pytest

import claude_3p_gui as app


def _resp(data: dict, status: int = 200) -> MagicMock:
    """Build a mock response object for urlopen."""
    m = MagicMock()
    m.read.return_value = json.dumps(data).encode("utf-8")
    m.getcode.return_value = status
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


class TestModelFetcher:
    def test_v1_models_success(self):
        resp = _resp({"data": [{"id": "m-1"}, {"id": "m-2"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp) as u:
            models = app.ModelFetcher.fetch("https://x.com/", "sk-test")
        assert models == ["m-1", "m-2"]
        called_url = u.call_args.args[0].full_url
        assert called_url == "https://x.com/v1/models"

    def test_deduplicates_and_sorts(self):
        resp = _resp({"data": [{"id": "b"}, {"id": "a"}, {"id": "b"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            assert app.ModelFetcher.fetch("https://x.com/", "sk") == ["a", "b"]

    def test_fallback_to_models_endpoint(self):
        """If /v1/models 404s, fall back to /models."""
        def side_effect(req, timeout=0):
            if req.full_url.endswith("/v1/models"):
                raise app.urllib.error.HTTPError(
                    req.full_url, 404, "Not Found", {}, None
                )
            return _resp({"data": [{"id": "m"}]})

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            assert app.ModelFetcher.fetch("https://x.com/", "sk") == ["m"]

    def test_401_surfaces_as_auth_error(self):
        def side_effect(req, timeout=0):
            raise app.urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, None
            )

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "鉴权失败" in str(exc.value)

    def test_timeout_error_message(self):
        import socket

        def side_effect(req, timeout=0):
            raise socket.timeout("timed out")

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "超时" in str(exc.value)

    def test_sends_expected_headers(self):
        resp = _resp({"data": [{"id": "m"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp) as u:
            app.ModelFetcher.fetch("https://x.com/", "sk-test")
        # Headers stored lowercase by Request.add_header's internals -> use .headers
        req = u.call_args.args[0]
        assert req.headers.get("Authorization".capitalize()) == "Bearer sk-test"
        assert req.headers.get("X-api-key") == "sk-test"
        assert req.headers.get("Anthropic-version") == "2023-06-01"

    def test_malformed_json_surfaces_as_fetch_error(self):
        resp = MagicMock()
        resp.read.return_value = b"<html>not json</html>"
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "响应格式异常" in str(exc.value)
```

- [ ] **Step 2: Confirm failure**

Run: `python3 -m pytest tests/test_model_fetcher.py -v`

Expected: tests fail with `AttributeError: module ... has no attribute 'ModelFetcher'` or `ModelFetchError`.

- [ ] **Step 3: Implement `ModelFetcher`**

In `claude_3p_gui.py`, below the `_timestamp` helper and before `class ConfigManager`:

```python
class ModelFetchError(Exception):
    """Raised when model listing cannot be obtained (with a user-facing message)."""


class ModelFetcher:
    """HTTP layer: try /v1/models then /models on a base URL."""

    @staticmethod
    def fetch(base_url: str, api_key: str, timeout: float = FETCH_TIMEOUT_SEC) -> list[str]:
        base_url = normalize_base_url(base_url)
        endpoints = [f"{base_url}v1/models", f"{base_url}models"]
        last_error: ModelFetchError | None = None
        for endpoint in endpoints:
            try:
                req = urllib.request.Request(endpoint, method="GET")
                req.add_header("Authorization", f"Bearer {api_key}")
                req.add_header("x-api-key", api_key)
                req.add_header("anthropic-version", "2023-06-01")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read()
                try:
                    parsed = json.loads(raw)
                except (ValueError, json.JSONDecodeError) as e:
                    raise ModelFetchError(f"响应格式异常: {e}") from e
                data = parsed.get("data") if isinstance(parsed, dict) else None
                if not data:
                    raise ModelFetchError("响应格式异常: 缺少 data 字段")
                ids = sorted({item["id"] for item in data if "id" in item})
                if not ids:
                    raise ModelFetchError("响应格式异常: 无模型 id")
                return ids
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise ModelFetchError(f"鉴权失败 ({e.code}),请检查 API Key") from e
                if 500 <= e.code < 600:
                    last_error = ModelFetchError(f"服务端错误 {e.code}")
                    continue
                if e.code == 404:
                    last_error = ModelFetchError(f"接口不存在 ({endpoint})")
                    continue
                last_error = ModelFetchError(f"HTTP 错误 {e.code}")
                continue
            except urllib.error.URLError as e:
                last_error = ModelFetchError(f"网络错误: {e.reason}")
                continue
            except TimeoutError:
                last_error = ModelFetchError("网络超时,请检查网络或 URL 可达性")
                continue
            except Exception as e:
                # Match socket.timeout (subclass of OSError on some Pythons)
                if "timed out" in str(e).lower():
                    last_error = ModelFetchError("网络超时,请检查网络或 URL 可达性")
                    continue
                last_error = ModelFetchError(f"未知错误: {e}")
                continue
        raise last_error or ModelFetchError("未知错误")
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_model_fetcher.py -v`

Expected: 7 passed.

- [ ] **Step 5: Run full test suite to confirm no regressions**

Run: `python3 -m pytest tests/ -v`

Expected: 26 passed (19 config + 7 fetcher).

- [ ] **Step 6: Commit**

```bash
git add claude_3p_gui.py tests/test_model_fetcher.py
git commit -m "feat: ModelFetcher with dual-endpoint + dual-auth fallback"
```

---

## Task 7: `App` window skeleton + URL radios + Key entry

**Goal:** Get the window rendering with URL radios and a Key entry. No fetch wiring yet.

**Files:**
- Modify: `claude_3p_gui.py` (replace `class App(tk.Tk): pass`)

- [ ] **Step 1: Implement window skeleton**

Replace `class App(tk.Tk): pass` with:

```python
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Claude Desktop 第三方网关配置")
        self.geometry("560x520")
        self.resizable(False, False)

        # Default font tuned for CJK on Windows
        try:
            self.option_add("*Font", "{Microsoft YaHei UI} 10")
        except tk.TclError:
            pass  # Font not installed (e.g. macOS during dev)

        self.config_mgr = ConfigManager()
        self._fetch_queue: queue.Queue = queue.Queue()
        self._model_vars: dict[str, tk.BooleanVar] = {}

        self._build_layout()

    def _build_layout(self) -> None:
        pad = {"padx": 12, "pady": 4}

        # --- Gateway URL radios ---
        ttk.Label(self, text="网关 URL:", font=("Microsoft YaHei UI", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", **pad
        )
        self.url_var = tk.StringVar(value=GATEWAYS[0])
        for i, url in enumerate(GATEWAYS, start=1):
            ttk.Radiobutton(
                self, text=url, value=url, variable=self.url_var
            ).grid(row=i, column=0, columnspan=3, sticky="w", padx=24)

        # --- API Key entry ---
        ttk.Label(self, text="API Key:").grid(
            row=4, column=0, sticky="w", **pad
        )
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(
            self, textvariable=self.key_var, show="•", width=48
        )
        self.key_entry.grid(row=4, column=1, sticky="we", padx=(0, 4), pady=4)
        self.show_key_btn = ttk.Button(
            self, text="\U0001f441", width=3, command=self._toggle_show_key
        )
        self.show_key_btn.grid(row=4, column=2, padx=(0, 12), pady=4)
        self.key_var.trace_add("write", lambda *_: self._update_fetch_button_state())

        # Placeholder for later tasks
        ttk.Separator(self, orient="horizontal").grid(
            row=99, column=0, columnspan=3, sticky="we", pady=8
        )

    def _toggle_show_key(self) -> None:
        current = self.key_entry.cget("show")
        self.key_entry.configure(show="" if current else "•")

    def _update_fetch_button_state(self) -> None:
        """Stub — fetch button is created in Task 8. Will enable/disable it."""
        pass
```

- [ ] **Step 2: Manual verify**

Run: `python3 /Users/apple/Desktop/Claude3pSetupWin/claude_3p_gui.py`

Expected behavior:
- Window appears, 560×520, titled "Claude Desktop 第三方网关配置".
- Three radio buttons with the three hardcoded URLs. First one (`pikachu`) is selected by default.
- API Key entry shows bullets as you type.
- Eye button next to Key entry: clicking it reveals/hides the text.
- No crash. Close the window.

Note: on macOS the `Microsoft YaHei UI` font won't be present; tkinter will fall back silently.

- [ ] **Step 3: Commit**

```bash
git add claude_3p_gui.py
git commit -m "feat(gui): window skeleton with URL radios and Key entry"
```

---

## Task 8: Fetch button + threaded fetch + checkbox list render

**Goal:** User clicks "拉取模型列表" → background thread calls `ModelFetcher.fetch` → result populates a scrollable checkbox list.

**Files:**
- Modify: `claude_3p_gui.py`

- [ ] **Step 1: Extend `_build_layout` with fetch button + status + list frame**

In `_build_layout`, replace the trailing `Separator` placeholder with:

```python
        # --- Fetch button + status ---
        self.fetch_btn = ttk.Button(
            self,
            text="拉取模型列表",
            command=self._on_fetch_click,
            state="disabled",
        )
        self.fetch_btn.grid(row=5, column=0, sticky="w", padx=12, pady=(12, 4))
        self.status_var = tk.StringVar(value="状态: 待输入 API Key")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.grid(row=5, column=1, columnspan=2, sticky="w", pady=(12, 4))

        # --- Model list (scrollable checkboxes) ---
        ttk.Label(self, text="可用模型:").grid(
            row=6, column=0, sticky="w", padx=12, pady=(8, 0)
        )

        list_frame = ttk.Frame(self, relief="sunken", borderwidth=1)
        list_frame.grid(
            row=7, column=0, columnspan=3, sticky="nsew", padx=12, pady=4
        )
        self.rowconfigure(7, weight=1)
        self.columnconfigure(1, weight=1)

        self._list_canvas = tk.Canvas(list_frame, height=180, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self._list_canvas.yview
        )
        self._list_inner = ttk.Frame(self._list_canvas)
        self._list_inner.bind(
            "<Configure>",
            lambda _e: self._list_canvas.configure(
                scrollregion=self._list_canvas.bbox("all")
            ),
        )
        self._list_canvas.create_window((0, 0), window=self._list_inner, anchor="nw")
        self._list_canvas.configure(yscrollcommand=scrollbar.set)
        self._list_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
```

- [ ] **Step 2: Update `_update_fetch_button_state` to reflect key emptiness**

Replace the stub with:

```python
    def _update_fetch_button_state(self) -> None:
        has_key = bool(self.key_var.get().strip())
        self.fetch_btn.configure(state="normal" if has_key else "disabled")
        if not has_key:
            self.status_var.set("状态: 待输入 API Key")
```

- [ ] **Step 3: Implement fetch click handler + polling**

Add these methods to `App`:

```python
    def _on_fetch_click(self) -> None:
        api_key = self.key_var.get().strip()
        url = self.url_var.get()
        if not api_key:
            return
        self.fetch_btn.configure(state="disabled")
        self.status_var.set("状态: 拉取中...")
        self._clear_model_list()
        threading.Thread(
            target=self._fetch_worker,
            args=(url, api_key),
            daemon=True,
        ).start()
        self.after(100, self._poll_fetch_queue)

    def _fetch_worker(self, url: str, api_key: str) -> None:
        try:
            models = ModelFetcher.fetch(url, api_key)
            self._fetch_queue.put(("ok", models))
        except ModelFetchError as e:
            self._fetch_queue.put(("error", str(e)))
        except Exception as e:
            self._fetch_queue.put(("error", f"未知错误: {e}"))

    def _poll_fetch_queue(self) -> None:
        try:
            kind, payload = self._fetch_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_fetch_queue)
            return
        self.fetch_btn.configure(state="normal")
        if kind == "ok":
            self._render_models(payload, check_default=True)
            self.status_var.set(f"状态: 已获取 {len(payload)} 个模型")
        else:
            self.status_var.set(f"状态: {payload}")
            # Manual-input fallback UI is added in Task 9

    def _clear_model_list(self) -> None:
        for child in self._list_inner.winfo_children():
            child.destroy()
        self._model_vars.clear()

    def _render_models(self, models: list[str], check_default: bool) -> None:
        self._clear_model_list()
        for name in models:
            var = tk.BooleanVar(value=check_default)
            ttk.Checkbutton(
                self._list_inner, text=name, variable=var
            ).pack(anchor="w", padx=6, pady=1)
            self._model_vars[name] = var
```

- [ ] **Step 4: Manual verify**

Run: `python3 /Users/apple/Desktop/Claude3pSetupWin/claude_3p_gui.py`

Test cases:
1. Type a fake key → "拉取模型列表" enables, status shows nothing.
2. Click fetch → status changes to "拉取中..." briefly, then "状态: 鉴权失败..." or "网络错误..." (expected since we're not on a real endpoint). No crash.
3. (If you have a real key for one of the three URLs, test that too — the list should render checkboxes, all checked by default.)

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py
git commit -m "feat(gui): threaded model fetch and checkbox list render"
```

---

## Task 9: Select all / clear all + manual fallback

**Goal:** Add "全选" / "全清" buttons. When fetch fails, swap the list area for a manual-entry fallback (single-line Entry + "应用" button that parses comma-separated model names and renders them as checkboxes).

**Files:**
- Modify: `claude_3p_gui.py`

- [ ] **Step 1: Add select/clear buttons and fallback widgets to `_build_layout`**

Add this block right after the "可用模型:" label, before `list_frame`:

```python
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=6, column=1, columnspan=2, sticky="e", padx=12, pady=(8, 0))
        ttk.Button(btn_frame, text="全选", command=self._select_all).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="全清", command=self._clear_all).pack(
            side="left", padx=2
        )
```

Add a manual-entry row below `list_frame` (row 8):

```python
        self.manual_frame = ttk.Frame(self)
        self.manual_frame.grid(row=8, column=0, columnspan=3, sticky="we", padx=12, pady=4)
        self.manual_frame.grid_remove()  # hidden until fetch failure
        ttk.Label(self.manual_frame, text="手动输入模型 (逗号分隔):").pack(
            side="left"
        )
        self.manual_var = tk.StringVar()
        ttk.Entry(self.manual_frame, textvariable=self.manual_var, width=40).pack(
            side="left", padx=4, fill="x", expand=True
        )
        ttk.Button(self.manual_frame, text="应用", command=self._apply_manual).pack(
            side="left"
        )
```

- [ ] **Step 2: Add the three command handlers**

```python
    def _select_all(self) -> None:
        for v in self._model_vars.values():
            v.set(True)

    def _clear_all(self) -> None:
        for v in self._model_vars.values():
            v.set(False)

    def _apply_manual(self) -> None:
        raw = self.manual_var.get()
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if not names:
            self.status_var.set("状态: 请输入至少一个模型名")
            return
        self._render_models(names, check_default=True)
        self.status_var.set(f"状态: 手动输入 {len(names)} 个模型")
```

- [ ] **Step 3: Show manual frame on fetch failure**

In `_poll_fetch_queue`, inside the `else:` branch (when `kind != "ok"`), add:

```python
            self.manual_frame.grid()
```

Also hide it on success:

```python
        if kind == "ok":
            self.manual_frame.grid_remove()
            self._render_models(payload, check_default=True)
            self.status_var.set(f"状态: 已获取 {len(payload)} 个模型")
```

- [ ] **Step 4: Manual verify**

Run the app. Test:
1. Fake key + fetch → status shows error, manual input row appears at the bottom.
2. Type `a,b,c` in manual entry, click "应用" → 3 checkboxes appear, all checked.
3. "全清" unchecks all; "全选" checks all.
4. Provide a valid URL/key combo and fetch successfully → manual row hides.

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py
git commit -m "feat(gui): select/clear all and manual model fallback"
```

---

## Task 10: Profile name + Write button + validation + Restart checkbox

**Goal:** Final row of controls: profile name entry, restart checkbox, "写入配置" and "退出" buttons, with proper validation and wiring.

**Files:**
- Modify: `claude_3p_gui.py`

- [ ] **Step 1: Append to `_build_layout` (row 9 onward)**

```python
        # --- Profile name + restart + action buttons ---
        bottom = ttk.Frame(self)
        bottom.grid(row=9, column=0, columnspan=3, sticky="we", padx=12, pady=(8, 0))
        ttk.Label(bottom, text="档案名:").pack(side="left")
        self.profile_var = tk.StringVar(value="Default")
        ttk.Entry(bottom, textvariable=self.profile_var, width=20).pack(
            side="left", padx=(4, 12)
        )
        self.restart_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            bottom, text="写入后重启 Claude Desktop", variable=self.restart_var
        ).pack(side="left")

        actions = ttk.Frame(self)
        actions.grid(row=10, column=0, columnspan=3, pady=(12, 4))
        ttk.Button(actions, text="写入配置", command=self._on_write_click).pack(
            side="left", padx=6
        )
        ttk.Button(actions, text="退出", command=self.destroy).pack(side="left", padx=6)
```

- [ ] **Step 2: Implement `_on_write_click`**

```python
    def _on_write_click(self) -> None:
        # Validate
        if not self.key_var.get().strip():
            messagebox.showwarning("校验失败", "请输入 API Key")
            return
        if not self.profile_var.get().strip():
            messagebox.showwarning("校验失败", "请输入档案名")
            return
        selected = [name for name, v in self._model_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("校验失败", "请至少选择一个模型")
            return
        if not self.config_mgr.claude_dir_exists():
            messagebox.showerror(
                "Claude Desktop 未找到",
                f"未找到配置目录: {self.config_mgr.base_dir}\n"
                "请先安装并启动 Claude Desktop 至少一次。",
            )
            return

        # Backup and write
        try:
            backup = self.config_mgr.backup_library()
            if backup is not None:
                self._log(f"已备份配置到: {backup}")
            base_url = normalize_base_url(self.url_var.get())
            profile_id = self.config_mgr.write_profile(
                name=self.profile_var.get().strip(),
                base_url=base_url,
                api_key=self.key_var.get().strip(),
                models=selected,
            )
            profile_file = self.config_mgr.lib_dir / f"{profile_id}.json"
            self._log(f"配置已写入: {profile_file}")
            self._log(f"档案 '{self.profile_var.get()}' 已设为激活")
        except Exception as e:
            messagebox.showerror("写入失败", str(e))
            return

        # Optional restart
        if self.restart_var.get():
            if self.config_mgr.restart_claude():
                self._log("已重启 Claude Desktop")
            else:
                self._log("未找到 Claude.exe,请手动启动")

        messagebox.showinfo("完成", "配置写入成功")
```

- [ ] **Step 3: Manual verify (on macOS — expected to warn about missing Claude Desktop)**

Run the app. Test:
1. Empty key → warn.
2. Type key but uncheck all models → warn.
3. Empty profile name → warn.
4. On macOS, full flow → "Claude Desktop 未找到" error (expected, no %APPDATA%).
5. No crash in any path.

- [ ] **Step 4: Commit**

```bash
git add claude_3p_gui.py
git commit -m "feat(gui): write button, validation, and restart flow"
```

---

## Task 11: Log area + final polish

**Goal:** Add a read-only log area at the bottom. Wire `_log()` to append messages. Clean up row/column weights.

**Files:**
- Modify: `claude_3p_gui.py`

- [ ] **Step 1: Add log widget to `_build_layout` (row 11)**

```python
        # --- Log area ---
        ttk.Label(self, text="日志:").grid(
            row=11, column=0, sticky="w", padx=12, pady=(12, 0)
        )
        self._log_text = tk.Text(self, height=5, state="disabled", wrap="word")
        self._log_text.grid(
            row=12, column=0, columnspan=3, sticky="nsew", padx=12, pady=(0, 12)
        )
```

- [ ] **Step 2: Implement `_log`**

```python
    def _log(self, msg: str) -> None:
        self._log_text.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.insert("end", f"[{ts}] {msg}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")
```

- [ ] **Step 3: Manual verify**

Run the app. Go through the write flow (use a made-up key); check that backup/write/restart messages appear in the log area with timestamps. Log area scrolls when full.

- [ ] **Step 4: Run full test suite**

Run: `python3 -m pytest tests/ -v`

Expected: 26 passed. (No regressions from GUI work — pure-logic tests still green.)

- [ ] **Step 5: Commit**

```bash
git add claude_3p_gui.py
git commit -m "feat(gui): log area with timestamped messages"
```

---

## Task 12: `build.bat` + README

**Files:**
- Create: `build.bat`
- Create: `README.md`

- [ ] **Step 1: Write `build.bat`**

```batch
@echo off
setlocal

echo === Installing build dependencies ===
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo === Running unit tests ===
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
if errorlevel 1 (
    echo Tests failed. Aborting build.
    pause
    exit /b 1
)

echo.
echo === Building executable ===
python -m PyInstaller --noconfirm --onefile --windowed --name Claude3pSetup claude_3p_gui.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo === Build complete: dist\Claude3pSetup.exe ===
pause
```

- [ ] **Step 2: Write `README.md`**

```markdown
# Claude3pSetup (Windows GUI)

一个图形化配置工具,用于把 Claude Desktop (Windows, 已开启 Developer Mode) 指向以下三个固定的第三方网关之一:

- `https://pikachu.claudecode.love`
- `https://dk.claudecode.love`
- `http://154.12.51.83`

功能对标项目根目录的 `claude-3p-setup.ps1`,但 URL 仅限上述三个(不支持自定义)。

## 使用 (已打包好的 exe)

1. 双击 `Claude3pSetup.exe`
2. 选择网关 URL
3. 输入 API Key (sk-...)
4. 点 "拉取模型列表"
5. 勾选要启用的模型
6. 填档案名 (默认 Default),决定是否勾选 "写入后重启 Claude Desktop"
7. 点 "写入配置"

配置写入 `%APPDATA%\Claude-3p\configLibrary\{profileId}.json`,并更新 `_meta.json.appliedId`。

## 自行构建 (Windows)

需要 Python 3.10+ 和 pip。

```bat
git clone <this-repo>
cd Claude3pSetupWin
build.bat
```

构建产物: `dist\Claude3pSetup.exe`。

## 开发 (任意平台)

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
python claude_3p_gui.py   # 运行 GUI (macOS/Linux 可调试,但写入路径仅 Windows 可用)
```

## 交叉构建说明

PyInstaller 不支持交叉编译: 在 macOS/Linux 上运行 PyInstaller 只能产出对应平台的二进制。生成 `.exe` 必须在 Windows 上运行 `build.bat`,或在 CI (如 GitHub Actions `windows-latest`) 里构建。
```

- [ ] **Step 3: Commit**

```bash
git add build.bat README.md
git commit -m "build: Windows build script and README"
```

---

## Task 13: Windows acceptance test

**Goal:** Run the full manual acceptance checklist from spec §8 on a Windows machine with Claude Desktop already installed and launched at least once.

**Prereq:**
- Windows machine/VM with Python 3.10+
- Claude Desktop installed and started (so `%APPDATA%\Claude-3p` exists)
- Valid API key for at least one of the three gateways

- [ ] **Step 1: Transfer the project to Windows**

Zip `/Users/apple/Desktop/Claude3pSetupWin` (excluding `.git`) and copy to the Windows box, or push to a git remote and clone.

- [ ] **Step 2: Run `build.bat`**

In a cmd/PowerShell window in the project folder:

```
build.bat
```

Expected: pytest passes, PyInstaller produces `dist\Claude3pSetup.exe`.

- [ ] **Step 3: Run the executable and go through the acceptance checklist**

Execute each item from spec §8. Record PASS / FAIL:

- [ ] Launch `Claude3pSetup.exe` — no error, window centered.
- [ ] Three URL radios visible, first one selected.
- [ ] Key entry shows `•`; eye button toggles plaintext.
- [ ] Fetch button disabled when Key empty.
- [ ] Bad Key → "鉴权失败" status and manual input row appears.
- [ ] Unreachable URL / disabled network → "网络超时" or "网络错误" status.
- [ ] Valid Key + reachable URL → models render, all checked by default.
- [ ] "全选" / "全清" buttons work.
- [ ] Empty profile name + write → validation warning.
- [ ] Write succeeds → `%APPDATA%\Claude-3p\configLibrary\{guid}.json` appears with correct fields.
- [ ] `_meta.json.appliedId` equals that guid.
- [ ] Writing same profile name twice → same guid is reused (one entry in `_meta.json`).
- [ ] Restart checkbox + write → Claude Desktop is killed and restarted.
- [ ] `configLibrary.bak-{timestamp}` directory created on write.

- [ ] **Step 4: Fix any failures inline**

If an item fails, reproduce locally (macOS) where possible, fix, re-run tests, re-run `build.bat` on Windows, re-verify. Commit fixes:

```bash
git commit -am "fix: <issue>"
```

- [ ] **Step 5: Final commit marking release**

```bash
git commit --allow-empty -m "release: Claude3pSetup v1.0.0 — acceptance passed"
```

---

## Done

After Task 13 passes, the deliverables are:
- `dist\Claude3pSetup.exe` (the user-facing product)
- `claude_3p_gui.py` + `tests/` (source + unit tests)
- `build.bat`, `README.md`, `requirements-*.txt` (repeatable builds)
- Spec and plan committed under `docs/superpowers/`
