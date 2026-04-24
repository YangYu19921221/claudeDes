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
