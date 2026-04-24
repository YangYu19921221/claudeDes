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


class ModelFetcher:
    pass


class App(tk.Tk):
    pass


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
