"""
PrincePDF - Application Configuration and Settings Manager
Handles user preferences, recent files, and UI state persistence.
"""

import json
import os
from typing import List, Dict, Any

CONFIG_FILE = os.path.expanduser("~/.princepdf_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "dark",             # "dark" or "light"
    "view_mode": "continuous",    # "single", "continuous", "side_by_side"
    "zoom_mode": "fit_width",     # "fit_width", "fit_page", "custom"
    "custom_zoom": 1.0,           # 1.0 = 100%
    "night_mode": False,          # Invert document colors for night reading
    "sidebar_visible": True,
    "sidebar_tab": 0,             # 0 = Thumbnails, 1 = Outline, 2 = Search
    "recent_files": [],           # List of recently opened paths
    "max_recent_files": 10,
    "window_geometry": None,      # (x, y, w, h)
    "window_maximized": True,
}


class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        self.data: Dict[str, Any] = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception:
                pass

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def add_recent_file(self, filepath: str):
        if not os.path.exists(filepath):
            return
        abs_path = os.path.abspath(filepath)
        recents: List[str] = [p for p in self.data.get("recent_files", []) if p != abs_path and os.path.exists(p)]
        recents.insert(0, abs_path)
        max_r = self.data.get("max_recent_files", 10)
        self.data["recent_files"] = recents[:max_r]
        self.save()

    def get_recent_files(self) -> List[str]:
        valid = [p for p in self.data.get("recent_files", []) if os.path.exists(p)]
        if len(valid) != len(self.data.get("recent_files", [])):
            self.data["recent_files"] = valid
            self.save()
        return valid

    def clear_recent_files(self):
        self.data["recent_files"] = []
        self.save()
