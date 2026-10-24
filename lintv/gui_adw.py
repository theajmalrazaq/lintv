"""
LinTV - GTK 4 + Libadwaita Interface (Linux Native)
Modern GNOME desktop client for controlling Android TV over Tailscale & ADB.
"""

import os
import sys
import threading
from typing import Dict, Optional, Any

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

from .config import ConfigManager
from .device import TVDeviceManager, KEYCODES
from .engine import TVStreamingEngine

APP_CSS = b"""
.remote-surface {
    background-color: alpha(@window_fg_color, 0.035);
    border-radius: 18px;
    padding: 14px 16px;
    border: 1px solid alpha(@window_fg_color, 0.07);
}

.hero-stream-btn {
    min-height: 48px;
    font-size: 15px;
    font-weight: 700;
    border-radius: 12px;
}

.dpad-center {
    background-color: @accent_bg_color;
    color: @accent_fg_color;
    border-radius: 28px;
    min-width: 58px;
    min-height: 58px;
    font-size: 15px;
    font-weight: 800;
    padding: 0;
}
.dpad-center:hover {
    filter: brightness(1.12);
}

.dpad-btn {
    border-radius: 16px;
    min-width: 52px;
    min-height: 44px;
    padding: 0;
}

.dpad-btn-h {
    border-radius: 16px;
    min-width: 44px;
    min-height: 52px;
    padding: 0;
}

.remote-pill-btn {
    min-height: 38px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 13px;
    padding: 4px 10px;
}

.power-btn {
    background-color: alpha(#e01b24, 0.12);
    color: #ff7b63;
    border-radius: 10px;
    min-height: 38px;
    font-weight: 600;
    font-size: 13px;
    padding: 4px 10px;
}

.power-btn:hover {
    background-color: alpha(#e01b24, 0.25);
    color: #ffffff;
}

.app-tile {
    min-height: 40px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 13px;
    padding: 6px 8px;
}
"""


def _create_icon_button(label: str, icon_name: str, css_class: Optional[str] = None) -> Gtk.Button:
    btn = Gtk.Button()
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    box.set_halign(Gtk.Align.CENTER)
    
    img = Gtk.Image.new_from_icon_name(icon_name)
    box.append(img)
    
    lbl = Gtk.Label(label=label)
    box.append(lbl)
    
    btn.set_child(box)
    if css_class:
        btn.add_css_class(css_class)
    return btn


class LinTVAdwApp(Adw.Application):
    def __init__(self, config: Optional[ConfigManager] = None):
        super().__init__(
            application_id="io.github.theajmalrazaq.lintv",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.config = config or ConfigManager()
        self.device_mgr = TVDeviceManager(self.config)
        self.engine = TVStreamingEngine()
        self.window: Optional[LinTVWindow] = None

    def do_activate(self):
        self._load_styles()
        if not self.window:
            self.window = LinTVWindow(self)
        self.window.present()
        self.device_mgr.start_monitoring(interval=2.5)

    def _load_styles(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(APP_CSS)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )


class LinTVWindow(Adw.ApplicationWindow):
    def __init__(self, app: LinTVAdwApp):
        super().__init__(application=app, title="LinTV")
        self.app = app
        self.config = app.config
        self.set_default_size(480, 780)
        self.set_size_request(380, 520)

        # Main Layout
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        # Header Bar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(self._build_header_title())
        main_box.append(self.header)

        # Settings Header Button (Target TV Config)
        btn_settings = Gtk.Button(icon_name="emblem-system-symbolic")
        btn_settings.set_tooltip_text("Device Settings (Tailscale IP & Port)")
        btn_settings.connect("clicked", lambda b: self._open_device_dialog())
        self.header.pack_end(btn_settings)

        # Refresh Header Button
        btn_refresh = Gtk.Button(icon_name="view-refresh-symbolic")
        btn_refresh.set_tooltip_text("Refresh Connection")
        btn_refresh.connect("clicked", lambda b: self._refresh_status())
        self.header.pack_end(btn_refresh)

        # Scrolled Body
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.append(self.scrolled)

        clamp = Adw.Clamp(maximum_size=460)
        self.scrolled.set_child(clamp)

        body_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        body_box.set_margin_top(12)
        body_box.set_margin_bottom(20)
        body_box.set_margin_start(16)
        body_box.set_margin_end(16)
        clamp.set_child(body_box)

        # 1. Connection Status Card
        status_group = Adw.PreferencesGroup(title="Device")
        self.row_status = Adw.ActionRow(
            title="Checking TV Status...",
            subtitle="Testing Tailscale &amp; Network connectivity..."
        )
        self.row_status.add_prefix(self._get_tv_icon())

        # Edit button inside status card
        btn_edit_device = Gtk.Button(icon_name="document-edit-symbolic")
        btn_edit_device.set_tooltip_text("Configure TV IP / Port")
        btn_edit_device.add_css_class("flat")
        btn_edit_device.connect("clicked", lambda b: self._open_device_dialog())
        self.row_status.add_suffix(btn_edit_device)

        self.badge_status = Gtk.Label(label="Connecting...")
        self.badge_status.add_css_class("caption")
        self.badge_status.add_css_class("pill")
        self.row_status.add_suffix(self.badge_status)

        status_group.add(self.row_status)
        body_box.append(status_group)

        # 2. Hero Watch & Control TV Button
        self.btn_stream = Gtk.Button()
        self.btn_stream_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_stream_box.set_halign(Gtk.Align.CENTER)
        self.btn_stream_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.btn_stream_label = Gtk.Label(label="Watch & Control TV")
        self.btn_stream_label.add_css_class("title-4")
        self.btn_stream_box.append(self.btn_stream_icon)
        self.btn_stream_box.append(self.btn_stream_label)
        self.btn_stream.set_child(self.btn_stream_box)
        self.btn_stream.add_css_class("suggested-action")
        self.btn_stream.add_css_class("hero-stream-btn")
        self.btn_stream.connect("clicked", self._on_stream_toggle_clicked)
        body_box.append(self.btn_stream)

        # 3. TV Remote Control Card
        remote_group = Adw.PreferencesGroup(title="TV Remote")
        remote_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        remote_card.add_css_class("remote-surface")

        # Top Function Bar: Power, Home, Back, Mute
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_bar.set_homogeneous(True)

        btn_power = _create_icon_button("Power", "switch-off-symbolic", "power-btn")
        btn_power.set_tooltip_text("Wake / Sleep TV (Power)")
        btn_power.connect("clicked", lambda b: self._send_key(KEYCODES["power"]))
        top_bar.append(btn_power)

        btn_home = _create_icon_button("Home", "user-home-symbolic", "remote-pill-btn")
        btn_home.set_tooltip_text("TV Home Screen")
        btn_home.connect("clicked", lambda b: self._send_key(KEYCODES["home"]))
        top_bar.append(btn_home)

        btn_back = _create_icon_button("Back", "go-previous-symbolic", "remote-pill-btn")
        btn_back.set_tooltip_text("Back")
        btn_back.connect("clicked", lambda b: self._send_key(KEYCODES["back"]))
        top_bar.append(btn_back)

        btn_mute = _create_icon_button("Mute", "audio-volume-muted-symbolic", "remote-pill-btn")
        btn_mute.set_tooltip_text("Mute Audio")
        btn_mute.connect("clicked", lambda b: self._send_key(KEYCODES["mute"]))
        top_bar.append(btn_mute)

        remote_card.append(top_bar)

        # Directional Navigation D-Pad Grid
        dpad_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        dpad_container.set_halign(Gtk.Align.CENTER)
        dpad_container.set_margin_top(4)
        dpad_container.set_margin_bottom(4)

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)

        # Up
        btn_up = Gtk.Button(icon_name="pan-up-symbolic")
        btn_up.add_css_class("dpad-btn")
        btn_up.set_tooltip_text("Up")
        btn_up.connect("clicked", lambda b: self._send_key(KEYCODES["up"]))
        grid.attach(btn_up, 1, 0, 1, 1)

        # Left
        btn_left = Gtk.Button(icon_name="pan-start-symbolic")
        btn_left.add_css_class("dpad-btn-h")
        btn_left.set_tooltip_text("Left")
        btn_left.connect("clicked", lambda b: self._send_key(KEYCODES["left"]))
        grid.attach(btn_left, 0, 1, 1, 1)

        # Center OK
        btn_ok = Gtk.Button(label="OK")
        btn_ok.add_css_class("dpad-center")
        btn_ok.set_tooltip_text("Select / OK")
        btn_ok.connect("clicked", lambda b: self._send_key(KEYCODES["ok"]))
        grid.attach(btn_ok, 1, 1, 1, 1)

        # Right
        btn_right = Gtk.Button(icon_name="pan-end-symbolic")
        btn_right.add_css_class("dpad-btn-h")
        btn_right.set_tooltip_text("Right")
        btn_right.connect("clicked", lambda b: self._send_key(KEYCODES["right"]))
        grid.attach(btn_right, 2, 1, 1, 1)

        # Down
        btn_down = Gtk.Button(icon_name="pan-down-symbolic")
        btn_down.add_css_class("dpad-btn")
        btn_down.set_tooltip_text("Down")
        btn_down.connect("clicked", lambda b: self._send_key(KEYCODES["down"]))
        grid.attach(btn_down, 1, 2, 1, 1)

        dpad_container.append(grid)
        remote_card.append(dpad_container)

        # Bottom Volume Bar
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_box.set_homogeneous(True)

        btn_vol_down = _create_icon_button("Volume  -", "audio-volume-low-symbolic", "remote-pill-btn")
        btn_vol_down.set_tooltip_text("Decrease Volume")
        btn_vol_down.connect("clicked", lambda b: self._send_key(KEYCODES["voldown"]))
        vol_box.append(btn_vol_down)

        btn_vol_up = _create_icon_button("Volume  +", "audio-volume-high-symbolic", "remote-pill-btn")
        btn_vol_up.set_tooltip_text("Increase Volume")
        btn_vol_up.connect("clicked", lambda b: self._send_key(KEYCODES["volup"]))
        vol_box.append(btn_vol_up)

        remote_card.append(vol_box)
        remote_group.add(remote_card)
        body_box.append(remote_group)

        # 4. Quick Launch TV Apps
        self.apps_group = Adw.PreferencesGroup(title="TV Apps")
        self._build_apps_grid()
        body_box.append(self.apps_group)

        # 5. Streaming Preferences as ExpanderRow
        settings_group = Adw.PreferencesGroup()
        fps_label = "60 FPS (Smooth)" if self.config.fps == 60 else "30 FPS (Low Latency)"
        codec_label = self.config.codec.upper()
        self.expander_settings = Adw.ExpanderRow(
            title="Stream Settings",
            subtitle=f"{fps_label} • {codec_label}"
        )
        self.combo_fps = Adw.ComboRow(title="Frame Rate")
        self.combo_fps.set_model(Gtk.StringList.new(["60 FPS (Smooth)", "30 FPS (Low Latency)"]))
        self.combo_fps.set_selected(0 if self.config.fps == 60 else 1)
        self.combo_fps.connect("notify::selected", self._on_settings_changed)
        self.expander_settings.add_row(self.combo_fps)

        self.combo_codec = Adw.ComboRow(title="Video Codec")
        self.combo_codec.set_model(Gtk.StringList.new(["H.264 (Recommended)", "H.265 (HEVC)"]))
        self.combo_codec.set_selected(0 if self.config.codec.lower() == "h264" else 1)
        self.combo_codec.connect("notify::selected", self._on_settings_changed)
        self.expander_settings.add_row(self.combo_codec)

        settings_group.add(self.expander_settings)
        body_box.append(settings_group)

        # Give top hero button initial focus so window doesn't scroll down
        self.set_default_widget(self.btn_stream)
        self.set_focus(self.btn_stream)

        # Register status callback
        self.app.device_mgr.add_listener(lambda st: GLib.idle_add(self._apply_status_update, st))
        self._refresh_status()

        # If unconfigured on first launch, open config dialog
        if not self.config.is_configured():
            GLib.timeout_add(400, self._open_device_dialog)

    def _get_tv_icon(self) -> Gtk.Image:
        tv_svg = "/usr/share/icons/Adwaita/symbolic/devices/tv-symbolic.svg"
        if os.path.exists(tv_svg):
            f = Gio.File.new_for_path(tv_svg)
            return Gtk.Image.new_from_gicon(Gio.FileIcon.new(f))
        return Gtk.Image.new_from_icon_name("user-desktop-symbolic")

    def _build_header_title(self) -> Gtk.Box:
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_valign(Gtk.Align.CENTER)

        lbl_title = Gtk.Label(label="LinTV")
        lbl_title.add_css_class("heading")

        self.lbl_subtitle = Gtk.Label(label="Android TV Remote")
        self.lbl_subtitle.add_css_class("caption")
        self.lbl_subtitle.add_css_class("dim-label")

        title_box.append(lbl_title)
        title_box.append(self.lbl_subtitle)
        return title_box

    def _build_apps_grid(self):
        apps = self.config.custom_apps or []
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        # 3 columns per row
        row_box = None
        for i, app_info in enumerate(apps):
            if i % 3 == 0:
                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row_box.set_homogeneous(True)
                container.append(row_box)
            
            btn = Gtk.Button(label=app_info.get("name", "App"))
            btn.add_css_class("app-tile")
            pkg = app_info.get("package", "")
            btn.connect("clicked", lambda b, p=pkg: self._launch_app(p))
            if row_box:
                row_box.append(btn)

        self.apps_group.set_child(container)

    def _on_settings_changed(self, combo, param):
        fps = 60 if self.combo_fps.get_selected() == 0 else 30
        codec = "h264" if self.combo_codec.get_selected() == 0 else "h265"
        self.config.fps = fps
        self.config.codec = codec
        self.config.save()
        fps_text = "60 FPS (Smooth)" if fps == 60 else "30 FPS (Low Latency)"
        self.expander_settings.set_subtitle(f"{fps_text} • {codec.upper()}")

    def _open_device_dialog(self):
        dialog = Adw.Window(title="Device Settings")
        dialog.set_modal(True)
        dialog.set_transient_for(self)
        dialog.set_default_size(380, 360)

        d_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dialog.set_content(d_box)

        d_header = Adw.HeaderBar()
        d_header.set_title_widget(Gtk.Label(label="Configure TV Device", css_classes=["heading"]))
        d_box.append(d_header)

        group = Adw.PreferencesGroup()
        group.set_margin_start(16)
        group.set_margin_end(16)
        group.set_margin_top(16)
        group.set_margin_bottom(16)

        entry_name = Adw.EntryRow(title="Device Name")
        entry_name.set_text(self.config.device_name)
        group.add(entry_name)

        entry_host = Adw.EntryRow(title="Tailscale IP or MagicDNS Host")
        entry_host.set_text(self.config.device_host)
        group.add(entry_host)

        entry_port = Adw.EntryRow(title="ADB Port (Default: 5555)")
        entry_port.set_text(str(self.config.device_port))
        group.add(entry_port)

        d_box.append(group)

        btn_save = Gtk.Button(label="Save & Connect")
        btn_save.add_css_class("suggested-action")
        btn_save.add_css_class("pill")
        btn_save.set_margin_start(20)
        btn_save.set_margin_end(20)
        btn_save.set_margin_bottom(20)

        def _do_save(b):
            host = entry_host.get_text().strip()
            name = entry_name.get_text().strip() or "Android TV"
            try:
                port = int(entry_port.get_text().strip() or "5555")
            except ValueError:
                port = 5555
            self.config.set_device(host=host, port=port, name=name)
            dialog.close()
            self._show_toast(f"Saved: {host}:{port}")
            self._refresh_status()

        btn_save.connect("clicked", _do_save)
        d_box.append(btn_save)

        dialog.present()

    def _apply_status_update(self, st: Dict[str, Any]):
        if not st.get("configured"):
            self.row_status.set_title("No Device Configured")
            self.row_status.set_subtitle("Click the settings button to enter Tailscale IP &amp; Port")
            self.badge_status.set_text("Unconfigured")
            self.badge_status.remove_css_class("success")
            self.badge_status.add_css_class("warning")
            self.btn_stream_label.set_text("Configure Device")
            self.lbl_subtitle.set_text("Not Configured")
            return

        name = st.get("name", "Android TV")
        serial = st.get("serial", "")
        connected = st.get("adb_connected", False)
        reachable = st.get("network_reachable", False)

        if reachable:
            if connected:
                self.row_status.set_title(f"{name} is Ready")
                self.row_status.set_subtitle(f"Connected to {serial}")
                self.badge_status.set_text("Connected")
                self.badge_status.remove_css_class("error")
                self.badge_status.remove_css_class("warning")
                self.badge_status.add_css_class("success")
                if not self.app.engine.is_running:
                    self.btn_stream_label.set_text("Watch & Control TV")
                    self.btn_stream_icon.set_from_icon_name("media-playback-start-symbolic")
                    self.btn_stream.remove_css_class("destructive-action")
                    self.btn_stream.add_css_class("suggested-action")
                self.lbl_subtitle.set_text(f"Online • {serial}")
            else:
                self.row_status.set_title(f"{name} is Online")
                self.row_status.set_subtitle(f"Reachable at {serial}. Connecting ADB...")
                self.badge_status.set_text("Online")
                self.badge_status.remove_css_class("error")
                self.badge_status.remove_css_class("success")
                self.badge_status.add_css_class("warning")
                if not self.app.engine.is_running:
                    self.btn_stream_label.set_text("Connect & Watch TV")
                self.lbl_subtitle.set_text(f"Online • {serial}")
        else:
            self.row_status.set_title(f"{name} is Offline")
            self.row_status.set_subtitle(f"Cannot reach {serial}. TV may be in standby.")
            self.badge_status.set_text("Offline")
            self.badge_status.remove_css_class("success")
            self.badge_status.remove_css_class("warning")
            self.badge_status.add_css_class("error")
            self.btn_stream_label.set_text("TV Offline (Standby)")
            self.lbl_subtitle.set_text("Offline (Standby)")

    def _refresh_status(self):
        def _check():
            st = self.app.device_mgr.probe_status()
            GLib.idle_add(self._apply_status_update, st)
        threading.Thread(target=_check, daemon=True).start()

    def _on_stream_toggle_clicked(self, btn: Gtk.Button):
        if not self.config.is_configured():
            self._open_device_dialog()
            return

        if self.app.engine.is_running:
            self.app.engine.stop_session()
            self._update_session_ui(False)
            return

        self._show_toast("Connecting to TV...")
        def _start_bg():
            serial = self.app.device_mgr.ensure_connected()
            def _done():
                if not serial:
                    self._show_toast("TV is currently offline or unreachable.")
                    return

                fps = self.config.fps
                codec = self.config.codec
                ok = self.app.engine.start_session(
                    serial=serial,
                    title=f"LinTV - {self.config.device_name}",
                    fps=fps,
                    codec=codec,
                    on_stop=lambda: GLib.idle_add(self._update_session_ui, False),
                    on_error=lambda err: GLib.idle_add(self._show_toast, f"Error: {err}"),
                )
                if ok:
                    self._update_session_ui(True)
                    self._show_toast("TV streaming session active.")
                else:
                    self._show_toast("Failed to launch scrcpy.")
            GLib.idle_add(_done)
        threading.Thread(target=_start_bg, daemon=True).start()

    def _update_session_ui(self, running: bool):
        if running:
            self.btn_stream_label.set_text("Stop TV Stream")
            self.btn_stream_icon.set_from_icon_name("media-playback-stop-symbolic")
            self.btn_stream.remove_css_class("suggested-action")
            self.btn_stream.add_css_class("destructive-action")
            self.lbl_subtitle.set_text("Screen Streaming Active")
        else:
            self.btn_stream_label.set_text("Watch & Control TV")
            self.btn_stream_icon.set_from_icon_name("media-playback-start-symbolic")
            self.btn_stream.remove_css_class("destructive-action")
            self.btn_stream.add_css_class("suggested-action")
            self._refresh_status()

    def _send_key(self, keycode: int):
        self.app.device_mgr.send_key(keycode)
        inv = {v: k.upper() for k, v in KEYCODES.items()}
        self._show_toast(f"Sent {inv.get(keycode, str(keycode))}")

    def _launch_app(self, pkg: str):
        if not pkg:
            return
        self.app.device_mgr.launch_app(pkg)
        self._show_toast(f"Launched {pkg.split('.')[-1].upper()} on TV")

    def _show_toast(self, message: str):
        toast = Adw.Toast(title=message, timeout=2)
        self.toast_overlay.add_toast(toast)
