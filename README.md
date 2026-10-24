# LinTV 📺

[![Release](https://github.com/theajmalrazaq/lintv/actions/workflows/release.yml/badge.svg)](https://github.com/theajmalrazaq/lintv/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-informational)](#installation)

**LinTV** is a fast, modern cross-platform desktop control center and low-latency remote screen streamer for **Android TV** and **Google TV** devices powered by **Tailscale mesh VPN** and **ADB / scrcpy**.

With LinTV, you can monitor, remotely control, and stream your Android TV screen smoothly from anywhere in the world — across local Wi-Fi or securely over the internet through Tailscale without configuring port forwarding or opening firewall holes.

---

## ✨ Features

- 🌐 **Zero-Config Remote Access via Tailscale:** Connect securely using your TV's Tailscale IP (`100.x.y.z`) or MagicDNS hostname (`my-tv.your-tailnet.ts.net`).
- ⚡ **Ultra Low-Latency Screen Mirroring:** Watch and control your TV screen at **60 FPS** in full HD using hardware-accelerated [scrcpy](https://github.com/Genymobile/scrcpy) (H.264 / H.265).
- 🎮 **Authentic TV Remote Control:** Directional navigation D-Pad (▲, ▼, ◀, ▶, OK), Power toggle, Home, Back, Volume +/-, and Mute.
- 🚀 **1-Click Quick TV App Launcher:** Launch streaming apps (YouTube, Netflix, Spotify, Prime Video, Plex, Kodi, or custom apps) directly from your desktop.
- ⌨️ **Keyboard Text Input:** Send search queries and text directly to the TV input field without typing with an on-screen remote.
- 🎨 **Adaptive Multiplatform GUI:**
  - **Linux:** Sleek native GNOME / Libadwaita interface with smooth dark styling.
  - **Windows & macOS:** Lightweight, modern dark-themed GUI with zero heavy runtime dependencies.
- 💻 **Complete CLI & Automation Engine:** Control power, volume, apps, or screen mirroring via terminal commands, scripts, or keyboard shortcuts.

---

## 📋 Prerequisites

Before using LinTV, ensure your client computer has:

1. **Python 3.8+**
2. **Android Debug Bridge (`adb`)**:
   - **Linux (Arch):** `sudo pacman -S android-tools`
   - **Linux (Debian/Ubuntu):** `sudo apt install adb`
   - **Linux (Fedora):** `sudo dnf install android-tools`
   - **Windows:** `winget install Google.PlatformTools` or `choco install adb`
   - **macOS:** `brew install android-platform-tools`
3. **scrcpy** (for screen mirroring):
   - **Linux:** `sudo pacman -S scrcpy` / `sudo apt install scrcpy` / `sudo dnf install scrcpy`
   - **Windows:** `winget install Genymobile.scrcpy` or `choco install scrcpy`
   - **macOS:** `brew install scrcpy`
4. **Tailscale** installed and connected on both your computer and your TV.

---

## 🛠️ Step-by-Step: Setting Up Tailscale on Android TV

Setting up Tailscale allows you to securely access your TV from outside your home without exposing your home router to the public internet.

```
+------------------+         Encrypted Tailscale Mesh VPN          +------------------+
|  Your Computer   | <===========================================> |    Android TV    |
| (Linux/Win/Mac)  |                                               |  (Tailscale App) |
|      LinTV       | ---- ADB Keyevents & Scrcpy Video Stream ---> |  ADB Port: 5555  |
+------------------+                                               +------------------+
```

### Step 1: Install Tailscale on your Android TV
- **Option A (Google Play Store):**
  1. Open the Google Play Store on your Android TV.
  2. Search for **Tailscale** and click **Install**.
- **Option B (Sideload APK if not in Play Store):**
  1. Download the official Android APK from [Tailscale Android Downloads](https://tailscale.com/download/android) or F-Droid.
  2. Transfer the APK to your TV using a USB flash drive or the **Send Files to TV (SFTV)** app from your smartphone.
  3. Install the APK using any file manager on the TV.

### Step 2: Sign In to Tailscale
1. Open the Tailscale app on your TV.
2. The screen will display a login URL or a **QR Code**.
3. Scan the QR code with your phone or visit the URL on your computer, then sign in with your Tailscale account.
4. Toggle the connection switch to **Connected** (a green dot will confirm active status).

### Step 3: Enable "Always-On VPN" & Background Battery Exemption (Crucial)
Android TV may terminate background apps during sleep. To ensure continuous reachability:
1. Go to your TV's **Settings** &rarr; **Network & Internet** &rarr; **VPN**.
2. Select **Tailscale** and toggle **Always-on VPN** to **ON**.
3. Go to **Settings** &rarr; **Apps** &rarr; **Special app access** &rarr; **Energy optimization** (or Battery Saver).
4. Find **Tailscale** and set it to **Don't optimize / Unrestricted**.

### Step 4: Enable Network Debugging (ADB over Wi-Fi/Tailscale)
1. Go to **Settings** &rarr; **Device Preferences** (or System) &rarr; **About**.
2. Scroll down to **Build** (or Android TV OS build) and click it **7 times** until a message displays: *"You are now a developer!"*.
3. Go back to **Device Preferences** &rarr; **Developer options**.
4. Enable **USB debugging**.
5. Enable **Network debugging** (or *Wireless debugging*). Android TV will listen on default port **5555**.

### Step 5: Authorize Your Computer on the TV Screen
When LinTV connects to the TV for the first time:
1. A prompt will appear on your TV screen:
   > *"Allow USB debugging? The computer's RSA key fingerprint is: XX:XX:..."*
2. Using your physical TV remote, check the box:
   ☑ **Always allow from this computer**
3. Select **OK** / **Allow**.

### Step 6: Find Your TV's Tailscale Address
1. Check the Tailscale app on your TV to view the assigned **100.x.y.z** address.
2. Alternatively, open your [Tailscale Admin Console](https://login.tailscale.com/admin/machines) and locate your TV's device name and IP (or MagicDNS hostname, e.g., `living-room-tv.tailnet.ts.net`).

---

## 📦 Installation

### Linux

#### Option 1: Quick Install (Recommended)
```bash
git clone https://github.com/theajmalrazaq/lintv.git
cd lintv
./install.sh
```
This installs the `lintv` executable to `~/.local/bin/` and registers the desktop launcher and icon.

#### Option 2: Pip Install
```bash
git clone https://github.com/theajmalrazaq/lintv.git
cd lintv
pip install -e .
```

---

### Windows

1. Download the latest `lintv-windows-x86_64.zip` from [GitHub Releases](https://github.com/theajmalrazaq/lintv/releases).
2. Extract the archive anywhere on your PC.
3. Ensure `adb` and `scrcpy` are installed (run in PowerShell: `winget install Google.PlatformTools Genymobile.scrcpy`).
4. Double-click `lintv.exe` to launch the application.

---

### macOS

1. Install prerequisites via Homebrew:
   ```bash
   brew install android-platform-tools scrcpy
   ```
2. Download `lintv-macos-x86_64.zip` from [GitHub Releases](https://github.com/theajmalrazaq/lintv/releases) or clone from source:
   ```bash
   git clone https://github.com/theajmalrazaq/lintv.git
   cd lintv
   pip3 install -e .
   lintv
   ```

---

## 🚀 How to Use

### 1. Graphical Interface (GUI)

Launch the interface by typing `lintv` in your terminal or opening **LinTV** from your system app menu.

```bash
lintv
```

1. **Configure Your TV:**
   - On first launch, click **Setup TV** (or the gear icon).
   - Enter your TV's **Tailscale IP or MagicDNS Host** (e.g., `100.x.y.z` or `living-room-tv.your-tailnet.ts.net`).
   - Enter the ADB port (`5555`).
   - Click **Save & Connect**.
2. **Watch Screen:** Click the prominent **Watch & Control TV** button to launch a 60 FPS screen mirror.
3. **Use Remote:** Click D-Pad arrows, OK, Power, Home, Back, or Volume buttons to navigate.
4. **Launch Apps:** Click any app tile (YouTube, Netflix, Spotify, Prime Video, Plex, etc.) to launch it immediately on the TV.

---

### 2. Command-Line Interface (CLI)

LinTV provides a full CLI for scripting, shortcuts, or headless environments:

#### Setup & Status
```bash
# Save your TV's Tailscale IP and port
lintv --set-host 100.x.y.z --set-port 5555 --set-name "Living Room TV"

# Check connection status
lintv --status
```

#### Screen Mirroring
```bash
# Start screen mirroring session
lintv --start

# Start mirroring in fullscreen with 60 FPS
lintv --start --fullscreen --fps 60

# Override host temporarily
lintv --host 100.x.y.z --start
```

#### Remote Hardware Keys
```bash
# Navigation
lintv --home          # Go to TV Home screen
lintv --back          # Go back
lintv --power         # Toggle TV standby / wake
lintv --mute          # Toggle mute

# Volume control
lintv --volup         # Increase volume
lintv --voldown       # Decrease volume

# D-Pad navigation
lintv --up
lintv --down
lintv --left
lintv --right
lintv --ok
```

#### App Launching & Text Input
```bash
# Launch installed apps by package name
lintv --app com.google.android.youtube.tv
lintv --app com.netflix.mediaclient
lintv --app com.spotify.tv.android

# Type text into active search field on TV
lintv --text "Blade Runner 2049"
```

---

## ⚙️ Configuration File

LinTV stores device profiles and user preferences in standard OS locations:

- **Linux:** `~/.config/lintv/config.json`
- **Windows:** `%APPDATA%\lintv\config.json`
- **macOS:** `~/Library/Application Support/lintv/config.json`

Example configuration:
```json
{
  "device_host": "100.x.y.z",
  "device_port": 5555,
  "device_name": "Living Room TV",
  "fps": 60,
  "codec": "h264",
  "stay_awake": true,
  "auto_connect": true,
  "custom_apps": [
    {"name": "YouTube", "package": "com.google.android.youtube.tv"},
    {"name": "Netflix", "package": "com.netflix.mediaclient"},
    {"name": "Spotify", "package": "com.spotify.tv.android"},
    {"name": "Prime Video", "package": "com.amazon.amazonvideo.livingroom"},
    {"name": "Plex", "package": "com.plexapp.android"},
    {"name": "Kodi", "package": "org.xbmc.kodi"}
  ]
}
```

---

## ❓ Troubleshooting

### 1. Device state shows `unauthorized`
- **Cause:** The TV has not authorized your computer's ADB key.
- **Fix:** Turn on the TV screen. An on-screen dialog *"Allow USB debugging?"* will be visible. Use your TV's physical remote to check **"Always allow from this computer"** and select **OK**.

### 2. Device state shows `offline`
- **Cause:** The ADB daemon held a stale socket connection to the TV.
- **Fix:** Restart your local ADB server:
  ```bash
  adb kill-server
  adb start-server
  lintv --status
  ```

### 3. TV is unreachable (`not_reachable` / `Offline`)
- Verify Tailscale is running on your computer (`tailscale status`).
- Verify Tailscale is active on your TV. If the TV was asleep, ensure **Always-on VPN** and battery optimization exemptions are configured according to [Step 3](#step-3-enable-always-on-vpn--background-battery-exemption-crucial).
- Test raw TCP connectivity:
  ```bash
  nc -zv <your-tv-tailscale-ip> 5555
  ```

### 4. scrcpy screen mirroring fails
- Check if scrcpy is installed and in your system PATH (`scrcpy --version`).
- If streaming over a high-latency connection, switch to 30 FPS or HEVC codec in Stream Settings.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
