"""
LinTV Device Manager
Handles network probing (Tailscale / LAN), ADB connection lifecycle, and hardware remote keyevents.
"""

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Any

from .config import ConfigManager

# Keycode Mappings
KEYCODES = {
    "home": 3,
    "back": 4,
    "up": 19,
    "down": 20,
    "left": 21,
    "right": 22,
    "volup": 24,
    "voldown": 25,
    "power": 26,
    "ok": 66,
    "menu": 82,
    "mute": 164,
    "sleep": 223,
    "wakeup": 224,
}


def find_adb_path() -> Optional[str]:
    """Finds the adb binary in PATH or common system directories."""
    # 1. Check PATH
    adb = shutil.which("adb")
    if adb:
        return adb

    # 2. Windows standard paths
    if sys.platform == "win32":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\platform-tools\adb.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\platform-tools\adb.exe"),
            r"C:\platform-tools\adb.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c

    # 3. macOS standard paths
    elif sys.platform == "darwin":
        candidates = [
            "/opt/homebrew/bin/adb",
            "/usr/local/bin/adb",
            os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"),
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c

    # 4. Linux standard paths
    else:
        candidates = [
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c

    return None


class TVDeviceManager:
    """Manages the network connection and ADB bridge to the target TV."""

    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.adb_bin = find_adb_path() or "adb"
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self.last_status: Dict[str, Any] = self._empty_status()

    def _empty_status(self) -> Dict[str, Any]:
        return {
            "configured": False,
            "host": "",
            "port": 5555,
            "serial": "",
            "name": "",
            "network_reachable": False,
            "adb_connected": False,
            "state": "unconfigured",
            "message": "No device configured. Set TV Tailscale IP or MagicDNS.",
        }

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]):
        """Adds a callback invoked when status changes."""
        self._listeners.append(callback)

    def is_network_reachable(self, host: str, port: int, timeout: float = 0.8) -> bool:
        """Tests if the host & port can be reached over TCP (Tailscale or LAN)."""
        if not host:
            return False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            res = s.connect_ex((host, int(port)))
            s.close()
            return res == 0
        except Exception:
            return False

    def get_adb_state(self, serial: str) -> str:
        """Returns the device state from adb: 'device', 'offline', 'unauthorized', or 'disconnected'."""
        if not serial:
            return "disconnected"
        try:
            res = subprocess.run(
                [self.adb_bin, "devices"],
                capture_output=True,
                text=True,
                timeout=2.0
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0] == serial:
                    return parts[1]
            return "disconnected"
        except Exception:
            return "disconnected"

    def connect_adb(self, host: str, port: int) -> bool:
        """Executes 'adb connect host:port'."""
        target = f"{host}:{port}"
        try:
            res = subprocess.run(
                [self.adb_bin, "connect", target],
                capture_output=True,
                text=True,
                timeout=4.0
            )
            out = res.stdout.lower()
            return "connected" in out or "already connected" in out
        except Exception:
            return False

    def disconnect_adb(self, host: str, port: int) -> bool:
        """Executes 'adb disconnect host:port'."""
        target = f"{host}:{port}"
        try:
            subprocess.run(
                [self.adb_bin, "disconnect", target],
                capture_output=True,
                text=True,
                timeout=3.0
            )
            return True
        except Exception:
            return False

    def ensure_connected(self) -> Optional[str]:
        """Probes the configured device and establishes ADB connection if reachable."""
        host = self.config.device_host
        port = self.config.device_port
        if not host:
            return None

        serial = f"{host}:{port}"

        # 1. Quick TCP socket probe
        if not self.is_network_reachable(host, port):
            return None

        # 2. Check current ADB state
        state = self.get_adb_state(serial)
        if state == "device":
            return serial

        # 3. If disconnected or offline, connect
        if self.connect_adb(host, port):
            # Recheck state
            time.sleep(0.3)
            if self.get_adb_state(serial) == "device":
                return serial

        return None

    def probe_status(self) -> Dict[str, Any]:
        """Probes current status and returns detailed telemetry."""
        host = self.config.device_host
        port = self.config.device_port
        name = self.config.device_name or "Android TV"

        if not host:
            st = self._empty_status()
            self.last_status = st
            return st

        serial = f"{host}:{port}"
        reachable = self.is_network_reachable(host, port)

        if not reachable:
            st = {
                "configured": True,
                "host": host,
                "port": port,
                "serial": serial,
                "name": name,
                "network_reachable": False,
                "adb_connected": False,
                "state": "not_reachable",
                "message": f"TV is Offline ({host}:{port} unreachable)",
            }
            self.last_status = st
            return st

        adb_state = self.get_adb_state(serial)
        if adb_state != "device" and self.config.auto_connect:
            self.connect_adb(host, port)
            time.sleep(0.2)
            adb_state = self.get_adb_state(serial)

        is_connected = (adb_state == "device")
        
        if is_connected:
            msg = f"Connected to {name} ({serial})"
        elif adb_state == "unauthorized":
            msg = "TV screen is requesting ADB Authorization! Click 'Always allow' on TV."
        elif adb_state == "offline":
            msg = "Device is in offline state. Try reconnecting."
        else:
            msg = f"TV is online at {serial}. Click Connect."

        st = {
            "configured": True,
            "host": host,
            "port": port,
            "serial": serial,
            "name": name,
            "network_reachable": True,
            "adb_connected": is_connected,
            "state": adb_state,
            "message": msg,
        }
        self.last_status = st
        return st

    def start_monitoring(self, interval: float = 2.5):
        """Starts background periodic polling of connection status."""
        if self._running:
            return
        self._running = True

        def _worker():
            while self._running:
                st = self.probe_status()
                for cb in self._listeners:
                    try:
                        cb(st)
                    except Exception:
                        pass
                time.sleep(interval)

        self._monitor_thread = threading.Thread(target=_worker, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stops background polling."""
        self._running = False

    def send_key(self, keycode: int) -> bool:
        """Sends an Android hardware keycode to the TV."""
        serial = self.ensure_connected()
        if not serial:
            return False
        try:
            subprocess.run(
                [self.adb_bin, "-s", serial, "shell", "input", "keyevent", str(keycode)],
                capture_output=True,
                timeout=2.0
            )
            return True
        except Exception:
            return False

    def send_key_name(self, name: str) -> bool:
        """Sends a named keycode ('home', 'back', 'power', etc.)."""
        code = KEYCODES.get(name.lower())
        if code is not None:
            return self.send_key(code)
        return False

    def send_text(self, text: str) -> bool:
        """Sends a text string to TV input fields (escapes spaces)."""
        serial = self.ensure_connected()
        if not serial:
            return False
        try:
            # Escape spaces for adb shell input text
            safe_text = text.replace(" ", "%s").replace("&", "\\&")
            subprocess.run(
                [self.adb_bin, "-s", serial, "shell", "input", "text", safe_text],
                capture_output=True,
                timeout=2.0
            )
            return True
        except Exception:
            return False

    def launch_app(self, package: str) -> bool:
        """Launches an installed app by package name."""
        serial = self.ensure_connected()
        if not serial:
            return False
        try:
            subprocess.run(
                [self.adb_bin, "-s", serial, "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
                timeout=3.0
            )
            return True
        except Exception:
            return False
