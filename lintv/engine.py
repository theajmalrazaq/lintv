"""
LinTV Streaming Engine
Manages scrcpy video streaming process, display options, and lifecycle.
"""

import os
import shutil
import subprocess
import sys
import threading
from typing import Callable, Optional, List


def find_scrcpy_path() -> Optional[str]:
    """Finds the scrcpy binary across platforms."""
    # 1. Check PATH
    scrcpy = shutil.which("scrcpy")
    if scrcpy:
        return scrcpy

    # 2. Windows paths
    if sys.platform == "win32":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\scrcpy\scrcpy.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\scrcpy\scrcpy.exe"),
            r"C:\scrcpy\scrcpy.exe",
            os.path.join(os.getcwd(), "scrcpy.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c

    # 3. macOS paths
    elif sys.platform == "darwin":
        candidates = [
            "/opt/homebrew/bin/scrcpy",
            "/usr/local/bin/scrcpy",
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c

    # 4. Linux paths
    else:
        candidates = [
            "/usr/bin/scrcpy",
            "/usr/local/bin/scrcpy",
            "/var/lib/flatpak/exports/bin/com.github.scrcpy",
        ]
        for c in candidates:
            if os.path.isfile(c) and os.access(c, os.X_OK):
                return c

    return None


class TVStreamingEngine:
    """Controls the scrcpy screen mirroring session."""

    def __init__(self):
        self.scrcpy_bin = find_scrcpy_path() or "scrcpy"
        self.process: Optional[subprocess.Popen] = None
        self._watcher_thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        """Returns True if a streaming session is currently active."""
        return self.process is not None and self.process.poll() is None

    def start_session(
        self,
        serial: str,
        title: str = "LinTV Remote Screen",
        fps: int = 60,
        codec: str = "h264",
        stay_awake: bool = True,
        fullscreen: bool = False,
        no_audio: bool = True,
        on_stop: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Launches a scrcpy streaming session."""
        if self.is_running:
            return True

        if not serial:
            if on_error:
                on_error("Target device serial/address is empty.")
            return False

        cmd = [
            self.scrcpy_bin,
            "-s", serial,
            f"--window-title={title}",
            f"--max-fps={fps}",
            f"--video-codec={codec}",
            "--keyboard=uhid",
        ]

        if stay_awake:
            cmd.append("--stay-awake")
        if fullscreen:
            cmd.append("--fullscreen")
        if no_audio:
            cmd.append("--no-audio")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            if on_error:
                on_error(f"scrcpy executable not found. Please install scrcpy.")
            return False
        except Exception as e:
            if on_error:
                on_error(str(e))
            return False

        def _watch():
            stdout, stderr = self.process.communicate()
            code = self.process.returncode
            self.process = None
            if code != 0 and stderr and on_error:
                on_error(stderr.strip())
            if on_stop:
                on_stop()

        self._watcher_thread = threading.Thread(target=_watch, daemon=True)
        self._watcher_thread.start()
        return True

    def stop_session(self):
        """Terminates the active scrcpy process."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.process = None
