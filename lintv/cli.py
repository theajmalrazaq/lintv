"""
LinTV Command-Line & Application Launcher Interface
Dispatches between GUI (Libadwaita / Tkinter) and headless CLI automation.
"""

import argparse
import sys
from typing import Optional

from .config import ConfigManager
from .device import TVDeviceManager, KEYCODES
from .engine import TVStreamingEngine


def launch_gui(gui_type: str = "auto", config: Optional[ConfigManager] = None):
    """Launches the best available GUI (Libadwaita on Linux, Tkinter fallback)."""
    cfg = config or ConfigManager()

    if gui_type in ("adw", "auto"):
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            gi.require_version("Adw", "1")
            from .gui_adw import LinTVAdwApp
            app = LinTVAdwApp(config=cfg)
            app.run(sys.argv[:1])
            return
        except (ImportError, ValueError) as e:
            if gui_type == "adw":
                print(f"[!] Error loading Libadwaita / GTK4: {e}", file=sys.stderr)
                sys.exit(1)

    # Tkinter Fallback
    try:
        from .gui_tk import LinTVTkApp
        tk_app = LinTVTkApp(config=cfg)
        tk_app.run()
    except Exception as e:
        print(f"[!] Failed to launch graphical interface: {e}", file=sys.stderr)
        print("[*] You can use LinTV directly via CLI: lintv --status or lintv --help")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="lintv",
        description="LinTV: Android TV Remote Control & Streaming Center via Tailscale & ADB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  lintv                                Launch graphical TV remote
  lintv --set-host 100.x.y.z           Save TV Tailscale IP as default
  lintv --status                       Check connection to TV
  lintv --start                        Stream TV screen immediately (scrcpy)
  lintv --home                         Send Home button to TV
  lintv --volup                        Turn volume up
  lintv --app com.netflix.mediaclient  Launch Netflix on TV
  lintv --text "Search query"          Type text into active field on TV
        """
    )

    # Target Device Overrides & Settings
    parser.add_argument("--host", metavar="IP_OR_DNS", help="Target device Tailscale IP or MagicDNS hostname")
    parser.add_argument("--port", type=int, metavar="PORT", help="Target ADB port (default: 5555)")
    parser.add_argument("--set-host", metavar="IP_OR_DNS", help="Save target host as default in config")
    parser.add_argument("--set-port", type=int, metavar="PORT", help="Save target port as default in config")
    parser.add_argument("--set-name", metavar="NAME", help="Save friendly device name in config")

    # Actions
    parser.add_argument("--status", action="store_true", help="Probe TV connection and show status")
    parser.add_argument("--start", "--stream", action="store_true", help="Start scrcpy screen mirroring session")
    parser.add_argument("--fullscreen", "-f", action="store_true", help="Mirror screen in fullscreen")
    parser.add_argument("--fps", type=int, choices=[30, 60], help="Screen streaming framerate (30 or 60)")
    parser.add_argument("--codec", choices=["h264", "h265"], help="Video codec (h264 or h265)")
    parser.add_argument("--gui", choices=["auto", "adw", "tk"], default="auto", help="GUI toolkit to use")

    # Remote Hardware Controls
    parser.add_argument("--power", action="store_true", help="Toggle TV power / standby")
    parser.add_argument("--home", action="store_true", help="Send Home key")
    parser.add_argument("--back", action="store_true", help="Send Back key")
    parser.add_argument("--mute", action="store_true", help="Toggle Mute")
    parser.add_argument("--volup", action="store_true", help="Increase Volume")
    parser.add_argument("--voldown", action="store_true", help="Decrease Volume")
    parser.add_argument("--up", action="store_true", help="Send D-Pad Up")
    parser.add_argument("--down", action="store_true", help="Send D-Pad Down")
    parser.add_argument("--left", action="store_true", help="Send D-Pad Left")
    parser.add_argument("--right", action="store_true", help="Send D-Pad Right")
    parser.add_argument("--ok", action="store_true", help="Send Select / OK key")
    parser.add_argument("--key", metavar="NAME_OR_CODE", help="Send custom keycode or name")
    parser.add_argument("--text", metavar="STR", help="Send text input to TV keyboard")
    parser.add_argument("--app", metavar="PKG", help="Launch an app package on TV")

    args, unknown = parser.parse_known_args()
    config = ConfigManager()

    # Handle persistent config changes
    changed = False
    if args.set_host:
        config.device_host = args.set_host
        changed = True
    if args.set_port:
        config.device_port = args.set_port
        changed = True
    if args.set_name:
        config.device_name = args.set_name
        changed = True
    if changed:
        config.save()
        print(f"[✓] Saved settings: {config.device_name} -> {config.device_host}:{config.device_port}")
        if not (args.status or args.start or any([args.power, args.home, args.back, args.volup, args.voldown, args.app, args.text])):
            return

    # Apply temporary runtime overrides
    if args.host:
        config.device_host = args.host
    if args.port:
        config.device_port = args.port

    mgr = TVDeviceManager(config)

    # 1. Status Check
    if args.status:
        st = mgr.probe_status()
        if not st["configured"]:
            print("[!] LinTV is not configured. Use: lintv --set-host <IP_OR_DNS>")
            sys.exit(1)
        if st["adb_connected"]:
            print(f"[✓] ONLINE & CONNECTED: {st['name']} at {st['serial']}")
        elif st["network_reachable"]:
            print(f"[~] ONLINE (Network reachable at {st['serial']}), ADB State: {st['state']}")
        else:
            print(f"[✗] OFFLINE: Cannot reach {st['serial']}. TV may be in standby.")
        return

    # 2. Remote Key Commands
    if args.power:
        mgr.send_key(KEYCODES["power"])
        print("[✓] Sent Power")
        return
    if args.home:
        mgr.send_key(KEYCODES["home"])
        print("[✓] Sent Home")
        return
    if args.back:
        mgr.send_key(KEYCODES["back"])
        print("[✓] Sent Back")
        return
    if args.mute:
        mgr.send_key(KEYCODES["mute"])
        print("[✓] Sent Mute")
        return
    if args.volup:
        mgr.send_key(KEYCODES["volup"])
        print("[✓] Sent Volume +")
        return
    if args.voldown:
        mgr.send_key(KEYCODES["voldown"])
        print("[✓] Sent Volume -")
        return
    if args.up:
        mgr.send_key(KEYCODES["up"])
        print("[✓] Sent D-Pad Up")
        return
    if args.down:
        mgr.send_key(KEYCODES["down"])
        print("[✓] Sent D-Pad Down")
        return
    if args.left:
        mgr.send_key(KEYCODES["left"])
        print("[✓] Sent D-Pad Left")
        return
    if args.right:
        mgr.send_key(KEYCODES["right"])
        print("[✓] Sent D-Pad Right")
        return
    if args.ok:
        mgr.send_key(KEYCODES["ok"])
        print("[✓] Sent OK")
        return
    if args.key:
        if args.key.isdigit():
            mgr.send_key(int(args.key))
        else:
            mgr.send_key_name(args.key)
        print(f"[✓] Sent Key: {args.key}")
        return
    if args.text:
        mgr.send_text(args.text)
        print(f"[✓] Sent Text: {args.text}")
        return
    if args.app:
        mgr.launch_app(args.app)
        print(f"[✓] Launched App: {args.app}")
        return

    # 3. Stream Session
    if args.start:
        if not config.is_configured():
            print("[!] No device configured. Set device first: lintv --set-host <IP_OR_DNS>", file=sys.stderr)
            sys.exit(1)

        print(f"[*] Connecting to {config.device_name} ({config.get_serial()})...")
        serial = mgr.ensure_connected()
        if not serial:
            st = mgr.probe_status()
            print(f"[!] Unable to connect: {st['message']}", file=sys.stderr)
            sys.exit(1)

        engine = TVStreamingEngine()
        fps = args.fps or config.fps
        codec = args.codec or config.codec
        print(f"[✓] Connected. Starting scrcpy mirror session ({fps} FPS, {codec.upper()})...")

        ok = engine.start_session(
            serial=serial,
            title=f"LinTV - {config.device_name}",
            fps=fps,
            codec=codec,
            fullscreen=args.fullscreen,
            on_error=lambda err: print(f"[!] Error: {err}", file=sys.stderr),
        )
        if not ok:
            sys.exit(1)

        try:
            if engine.process:
                engine.process.wait()
        except KeyboardInterrupt:
            print("\n[*] Stopping stream...")
            engine.stop_session()
        return

    # 4. Default: Launch Graphical Interface
    launch_gui(gui_type=args.gui, config=config)


if __name__ == "__main__":
    main()
