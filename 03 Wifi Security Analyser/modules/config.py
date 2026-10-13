"""Safe JSON-backed configuration for the desktop application."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config.json"
DEFAULT_CONFIG: dict[str, Any] = {"scan_interval": 10, "demo_mode": True, "auto_scan": False, "log_level": "INFO"}


class Config:
    """Loads, validates, and persists only supported configuration values."""
    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path, self.messages = path, []
        self.values = self.load()

    def load(self) -> dict[str, Any]:
        values = DEFAULT_CONFIG.copy()
        if not self.path.exists():
            self.messages.append("config.json was not found; safe defaults are in use.")
            return values
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict): raise ValueError("configuration must be a JSON object")
            values.update({key: raw[key] for key in DEFAULT_CONFIG if key in raw})
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.messages.append(f"Invalid config.json ignored: {exc}")
            return DEFAULT_CONFIG.copy()
        interval = values["scan_interval"]
        if not isinstance(interval, int) or isinstance(interval, bool) or not 1 <= interval <= 3600:
            self.messages.append("scan_interval must be an integer from 1 to 3600; using 10."); values["scan_interval"] = 10
        for key in ("demo_mode", "auto_scan"):
            if not isinstance(values[key], bool):
                self.messages.append(f"{key} must be true or false; using default."); values[key] = DEFAULT_CONFIG[key]
        if str(values["log_level"]).upper() not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            self.messages.append("log_level must be DEBUG, INFO, WARNING, or ERROR; using INFO."); values["log_level"] = "INFO"
        else: values["log_level"] = str(values["log_level"]).upper()
        return values

    def save(self) -> None:
        self.path.write_text(json.dumps(self.values, indent=2) + "\n", encoding="utf-8")
    def get(self, key: str, default: Any = None) -> Any: return self.values.get(key, default)
    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULT_CONFIG: raise KeyError(f"Unsupported configuration key: {key}")
        self.values[key] = value; self.save()


config = Config()
