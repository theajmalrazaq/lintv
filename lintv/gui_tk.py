"""
LinTV - Cross-Platform Tkinter Interface
Lightweight, native GUI for Windows, macOS, and Linux systems without GTK4.
"""

import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from .config import ConfigManager
from .device import TVDeviceManager, KEYCODES
from .engine import TVStreamingEngine


class LinTVTkApp:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.device_mgr = TVDeviceManager(self.config)
        self.engine = TVStreamingEngine()

        self.root = tk.Tk()
        self.root.title("LinTV - Android TV Remote")
        self.root.geometry("440x720")
        self.root.minsize(380, 600)
        self.root.configure(bg="#1e1e2e")

        self._apply_styles()
        self._build_ui()

        # Start background status polling
        self.device_mgr.add_listener(lambda st: self.root.after(0, self._apply_status_update, st))
        self.device_mgr.start_monitoring(interval=2.5)

    def _apply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Dark theme colors
        style.configure(".", background="#1e1e2e", foreground="#cdd6f4")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("Surface.TFrame", background="#282a36", relief="flat")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#cdd6f4")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#a6adc8")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        # 1. Header
        header_frame = ttk.Frame(main)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        lbl_title = ttk.Label(header_frame, text="LinTV", style="Header.TLabel")
        lbl_title.pack(side=tk.LEFT)

        btn_settings = tk.Button(
            header_frame,
            text="⚙ Setup TV",
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            command=self._open_config_dialog,
        )
        btn_settings.pack(side=tk.RIGHT)

        # 2. Connection Status Card
        card_status = tk.Frame(main, bg="#282a36", padx=14, pady=10)
        card_status.pack(fill=tk.X, pady=(0, 12))

        self.lbl_status_title = tk.Label(
            card_status,
            text="Checking TV Status...",
            bg="#282a36",
            fg="#cdd6f4",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.lbl_status_title.pack(fill=tk.X)

        self.lbl_status_sub = tk.Label(
            card_status,
            text="Probing Tailscale & Network...",
            bg="#282a36",
            fg="#a6adc8",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_status_sub.pack(fill=tk.X)

        # 3. Hero Watch & Control Button
        self.btn_stream = tk.Button(
            main,
            text="▶ Watch & Control TV",
            bg="#3584e4",
            fg="#ffffff",
            activebackground="#1c71d8",
            activeforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            pady=10,
            command=self._on_stream_clicked,
        )
        self.btn_stream.pack(fill=tk.X, pady=(0, 14))

        # 4. Remote Control Card
        remote_card = tk.Frame(main, bg="#282a36", padx=14, pady=12)
        remote_card.pack(fill=tk.X, pady=(0, 14))

        lbl_rem = tk.Label(remote_card, text="TV Remote", bg="#282a36", fg="#cdd6f4", font=("Segoe UI", 11, "bold"))
        lbl_rem.pack(anchor="w", pady=(0, 8))

        # Top Bar: Power, Home, Back, Mute
        top_bar = tk.Frame(remote_card, bg="#282a36")
        top_bar.pack(fill=tk.X, pady=(0, 10))

        btn_power = tk.Button(
            top_bar, text="Power", bg="#592020", fg="#ff7b63", relief="flat",
            activebackground="#7a2b2b", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), pady=6, command=lambda: self._send_key(KEYCODES["power"])
        )
        btn_power.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        btn_home = tk.Button(
            top_bar, text="Home", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), pady=6, command=lambda: self._send_key(KEYCODES["home"])
        )
        btn_home.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        btn_back = tk.Button(
            top_bar, text="Back", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), pady=6, command=lambda: self._send_key(KEYCODES["back"])
        )
        btn_back.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        btn_mute = tk.Button(
            top_bar, text="Mute", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), pady=6, command=lambda: self._send_key(KEYCODES["mute"])
        )
        btn_mute.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        # D-Pad
        dpad_frame = tk.Frame(remote_card, bg="#282a36")
        dpad_frame.pack(pady=6)

        btn_up = tk.Button(
            dpad_frame, text="▲", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", width=6, height=2,
            font=("Segoe UI", 11, "bold"), command=lambda: self._send_key(KEYCODES["up"])
        )
        btn_up.grid(row=0, column=1, padx=4, pady=4)

        btn_left = tk.Button(
            dpad_frame, text="◀", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", width=6, height=2,
            font=("Segoe UI", 11, "bold"), command=lambda: self._send_key(KEYCODES["left"])
        )
        btn_left.grid(row=1, column=0, padx=4, pady=4)

        btn_ok = tk.Button(
            dpad_frame, text="OK", bg="#3584e4", fg="#ffffff", relief="flat",
            activebackground="#1c71d8", width=6, height=2,
            font=("Segoe UI", 11, "bold"), command=lambda: self._send_key(KEYCODES["ok"])
        )
        btn_ok.grid(row=1, column=1, padx=4, pady=4)

        btn_right = tk.Button(
            dpad_frame, text="▶", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", width=6, height=2,
            font=("Segoe UI", 11, "bold"), command=lambda: self._send_key(KEYCODES["right"])
        )
        btn_right.grid(row=1, column=2, padx=4, pady=4)

        btn_down = tk.Button(
            dpad_frame, text="▼", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", width=6, height=2,
            font=("Segoe UI", 11, "bold"), command=lambda: self._send_key(KEYCODES["down"])
        )
        btn_down.grid(row=2, column=1, padx=4, pady=4)

        # Bottom Bar: Vol -, Vol +
        vol_bar = tk.Frame(remote_card, bg="#282a36")
        vol_bar.pack(fill=tk.X, pady=(10, 0))

        btn_voldown = tk.Button(
            vol_bar, text="🔉 Volume -", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", font=("Segoe UI", 9, "bold"), pady=6,
            command=lambda: self._send_key(KEYCODES["voldown"])
        )
        btn_voldown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        btn_volup = tk.Button(
            vol_bar, text="🔊 Volume +", bg="#313244", fg="#cdd6f4", relief="flat",
            activebackground="#45475a", font=("Segoe UI", 9, "bold"), pady=6,
            command=lambda: self._send_key(KEYCODES["volup"])
        )
        btn_volup.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        # 5. Quick Launch Apps
        apps_card = tk.Frame(main, bg="#282a36", padx=14, pady=12)
        apps_card.pack(fill=tk.X)

        lbl_apps = tk.Label(apps_card, text="TV Apps", bg="#282a36", fg="#cdd6f4", font=("Segoe UI", 11, "bold"))
        lbl_apps.pack(anchor="w", pady=(0, 8))

        apps_grid = tk.Frame(apps_card, bg="#282a36")
        apps_grid.pack(fill=tk.X)

        apps = self.config.custom_apps or []
        for i, app_info in enumerate(apps):
            r = i // 3
            c = i % 3
            name = app_info.get("name", "App")
            pkg = app_info.get("package", "")
            btn = tk.Button(
                apps_grid, text=name, bg="#313244", fg="#cdd6f4", relief="flat",
                activebackground="#45475a", font=("Segoe UI", 9), pady=6,
                command=lambda p=pkg: self._launch_app(p)
            )
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")
            apps_grid.columnconfigure(c, weight=1)

        # If not configured, prompt on launch
        if not self.config.is_configured():
            self.root.after(300, self._open_config_dialog)

    def _open_config_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configure TV Connection")
        dlg.geometry("380x280")
        dlg.configure(bg="#1e1e2e")
        dlg.transient(self.root)
        dlg.grab_set()

        pad = tk.Frame(dlg, bg="#1e1e2e", padx=20, pady=20)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text="TV Device Settings", font=("Segoe UI", 13, "bold"), bg="#1e1e2e", fg="#cdd6f4").pack(anchor="w", pady=(0, 10))

        tk.Label(pad, text="Device Name:", bg="#1e1e2e", fg="#a6adc8").pack(anchor="w")
        ent_name = tk.Entry(pad, bg="#313244", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("Segoe UI", 10))
        ent_name.insert(0, self.config.device_name)
        ent_name.pack(fill=tk.X, pady=(2, 8))

        tk.Label(pad, text="Tailscale IP or MagicDNS Host:", bg="#1e1e2e", fg="#a6adc8").pack(anchor="w")
        ent_host = tk.Entry(pad, bg="#313244", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("Segoe UI", 10))
        ent_host.insert(0, self.config.device_host)
        ent_host.pack(fill=tk.X, pady=(2, 8))

        tk.Label(pad, text="ADB Port (Default 5555):", bg="#1e1e2e", fg="#a6adc8").pack(anchor="w")
        ent_port = tk.Entry(pad, bg="#313244", fg="#ffffff", insertbackground="#ffffff", relief="flat", font=("Segoe UI", 10))
        ent_port.insert(0, str(self.config.device_port))
        ent_port.pack(fill=tk.X, pady=(2, 14))

        def _save():
            host = ent_host.get().strip()
            name = ent_name.get().strip() or "Android TV"
            try:
                port = int(ent_port.get().strip() or "5555")
            except ValueError:
                port = 5555
            self.config.set_device(host=host, port=port, name=name)
            dlg.destroy()
            self._refresh_status()

        btn_save = tk.Button(
            pad, text="Save & Connect", bg="#3584e4", fg="#ffffff", relief="flat",
            activebackground="#1c71d8", font=("Segoe UI", 10, "bold"), pady=8, command=_save
        )
        btn_save.pack(fill=tk.X)

    def _apply_status_update(self, st: Dict[str, Any]):
        if not st.get("configured"):
            self.lbl_status_title.config(text="No Device Configured", fg="#f9e2af")
            self.lbl_status_sub.config(text="Click 'Setup TV' to configure Tailscale IP & Port")
            self.btn_stream.config(text="Setup Device", bg="#45475a")
            return

        name = st.get("name", "Android TV")
        serial = st.get("serial", "")
        connected = st.get("adb_connected", False)
        reachable = st.get("network_reachable", False)

        if reachable:
            if connected:
                self.lbl_status_title.config(text=f"{name} is Ready", fg="#a6e3a1")
                self.lbl_status_sub.config(text=f"Connected to {serial}")
                if not self.engine.is_running:
                    self.btn_stream.config(text="▶ Watch & Control TV", bg="#3584e4")
            else:
                self.lbl_status_title.config(text=f"{name} is Online", fg="#89b4fa")
                self.lbl_status_sub.config(text=f"Reachable at {serial}. Connecting ADB...")
                if not self.engine.is_running:
                    self.btn_stream.config(text="Connect & Watch TV", bg="#3584e4")
        else:
            self.lbl_status_title.config(text=f"{name} is Offline", fg="#f38ba8")
            self.lbl_status_sub.config(text=f"Cannot reach {serial}. TV may be in standby.")
            self.btn_stream.config(text="TV Offline (Standby)", bg="#45475a")

    def _refresh_status(self):
        def _bg():
            st = self.device_mgr.probe_status()
            self.root.after(0, self._apply_status_update, st)
        threading.Thread(target=_bg, daemon=True).start()

    def _on_stream_clicked(self):
        if not self.config.is_configured():
            self._open_config_dialog()
            return

        if self.engine.is_running:
            self.engine.stop_session()
            self.btn_stream.config(text="▶ Watch & Control TV", bg="#3584e4")
            return

        def _start_bg():
            serial = self.device_mgr.ensure_connected()
            if not serial:
                self.root.after(0, lambda: messagebox.showwarning("LinTV", "TV is currently offline or unreachable."))
                return

            ok = self.engine.start_session(
                serial=serial,
                title=f"LinTV - {self.config.device_name}",
                fps=self.config.fps,
                codec=self.config.codec,
                on_stop=lambda: self.root.after(0, lambda: self.btn_stream.config(text="▶ Watch & Control TV", bg="#3584e4")),
                on_error=lambda err: self.root.after(0, lambda: messagebox.showerror("LinTV Error", err)),
            )
            if ok:
                self.root.after(0, lambda: self.btn_stream.config(text="⏹ Stop TV Stream", bg="#e01b24"))

        threading.Thread(target=_start_bg, daemon=True).start()

    def _send_key(self, code: int):
        self.device_mgr.send_key(code)

    def _launch_app(self, pkg: str):
        if pkg:
            self.device_mgr.launch_app(pkg)

    def run(self):
        self.root.mainloop()
