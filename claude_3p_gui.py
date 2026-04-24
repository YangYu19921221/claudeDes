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


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


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

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=6, column=1, columnspan=2, sticky="e", padx=12, pady=(8, 0))
        ttk.Button(btn_frame, text="全选", command=self._select_all).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="全清", command=self._clear_all).pack(
            side="left", padx=2
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

    def _toggle_show_key(self) -> None:
        current = self.key_entry.cget("show")
        self.key_entry.configure(show="" if current else "•")

    def _update_fetch_button_state(self) -> None:
        has_key = bool(self.key_var.get().strip())
        self.fetch_btn.configure(state="normal" if has_key else "disabled")
        if not has_key:
            self.status_var.set("状态: 待输入 API Key")


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
            self.manual_frame.grid_remove()
            self._render_models(payload, check_default=True)
            self.status_var.set(f"状态: 已获取 {len(payload)} 个模型")
        else:
            self.status_var.set(f"状态: {payload}")
            self.manual_frame.grid()

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


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
