"""
LinTV Configuration Manager
Handles cross-platform persistent storage of TV device addresses, preferences, and custom apps.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional

DEFAULT_APPS = [
    {"name": "YouTube", "package": "com.google.android.youtube.tv"},
    {"name": "Netflix", "package": "com.netflix.mediaclient"},
    {"name": "Spotify", "package": "com.spotify.tv.android"},
    {"name": "Prime Video", "package": "com.amazon.amazonvideo.livingroom"},
    {"name": "Plex", "package": "com.plexapp.android"},
    {"name": "Kodi", "package": "org.xbmc.kodi"}
]

DEFAULT_CONFIG: Dict[str, Any] = {
    "device_host": "",
    "device_port": 5555,
    "device_name": "Android TV",
    "fps": 60,
    "codec": "h264",
    "stay_awake": True,
    "auto_connect": True,
    "custom_apps": DEFAULT_APPS
}


def get_config_dir() -> str:
    """Returns the platform-specific configuration directory for LinTV."""
    custom_dir = os.environ.get("LINTV_CONFIG_DIR")
    if custom_dir:
        return os.path.abspath(custom_dir)

    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return os.path.join(appdata, "lintv")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/lintv")
    else:
        # Linux / BSD / POSIX
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(xdg_config, "lintv")


def get_config_file() -> str:
    """Returns the full path to config.json."""
    return os.path.join(get_config_dir(), "config.json")


class ConfigManager:
    """Manages reading and writing application settings."""

    def __init__(self):
        self.config_dir = get_config_dir()
        self.config_path = get_config_file()
        self._data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self.load()

    def load(self) -> Dict[str, Any]:
        """Loads configuration from disk, creating defaults if not present."""
        if not os.path.exists(self.config_path):
            self._data = dict(DEFAULT_CONFIG)
            return self._data

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    # Merge with default config to ensure all keys exist
                    for k, v in DEFAULT_CONFIG.items():
                        if k not in loaded:
                            loaded[k] = v
                    self._data = loaded
        except Exception:
            self._data = dict(DEFAULT_CONFIG)

        return self._data

    def save(self) -> bool:
        """Saves current configuration to disk atomically."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            tmp_path = self.config_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp_path, self.config_path)
            return True
        except Exception:
            return False

    @property
    def device_host(self) -> str:
        return self._data.get("device_host", "").strip()

    @device_host.setter
    def device_host(self, value: str):
        self._data["device_host"] = value.strip()

    @property
    def device_port(self) -> int:
        return int(self._data.get("device_port", 5555))

    @device_port.setter
    def device_port(self, value: int):
        self._data["device_port"] = int(value)

    @property
    def device_name(self) -> str:
        return self._data.get("device_name", "Android TV").strip()

    @device_name.setter
    def device_name(self, value: str):
        self._data["device_name"] = value.strip()

    @property
    def fps(self) -> int:
        return int(self._data.get("fps", 60))

    @fps.setter
    def fps(self, value: int):
        self._data["fps"] = int(value)

    @property
    def codec(self) -> str:
        return self._data.get("codec", "h264")

    @codec.setter
    def codec(self, value: str):
        self._data["codec"] = value

    @property
    def stay_awake(self) -> bool:
        return bool(self._data.get("stay_awake", True))

    @stay_awake.setter
    def stay_awake(self, value: bool):
        self._data["stay_awake"] = bool(value)

    @property
    def auto_connect(self) -> bool:
        return bool(self._data.get("auto_connect", True))

    @auto_connect.setter
    def auto_connect(self, value: bool):
        self._data["auto_connect"] = bool(value)

    @property
    def custom_apps(self) -> List[Dict[str, str]]:
        return self._data.get("custom_apps", DEFAULT_APPS)

    @custom_apps.setter
    def custom_apps(self, value: List[Dict[str, str]]):
        self._data["custom_apps"] = value

    def is_configured(self) -> bool:
        """Returns True if a device host address is configured."""
        return bool(self.device_host)

    def get_serial(self) -> str:
        """Returns the ADB serial target (host:port) or empty string."""
        if not self.device_host:
            return ""
        return f"{self.device_host}:{self.device_port}"

    def set_device(self, host: str, port: int = 5555, name: Optional[str] = None):
        """Updates device details and saves immediately."""
        self.device_host = host
        self.device_port = port
        if name:
            self.device_name = name
        self.save()
