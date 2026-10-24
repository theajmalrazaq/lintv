#!/usr/bin/env bash
# LinTV Linux Installation Script
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"

echo "=== Installing LinTV for Linux ==="

mkdir -p "${BIN_DIR}" "${APP_DIR}" "${ICON_DIR}"

# 1. Install CLI/GUI runner
chmod +x "${REPO_DIR}/bin/lintv"
ln -sf "${REPO_DIR}/bin/lintv" "${BIN_DIR}/lintv"
echo "[✓] Symlinked ${BIN_DIR}/lintv -> ${REPO_DIR}/bin/lintv"

# 2. Install Icon
cp "${REPO_DIR}/assets/lintv.svg" "${ICON_DIR}/io.github.theajmalrazaq.lintv.svg"
echo "[✓] Installed application icon"

# 3. Install Desktop Launcher
cat <<EOF > "${APP_DIR}/io.github.theajmalrazaq.lintv.desktop"
[Desktop Entry]
Name=LinTV
GenericName=Android TV Remote & Streamer
Comment=Control and watch Android TV over Tailscale VPN and ADB
Exec=${BIN_DIR}/lintv
Icon=io.github.theajmalrazaq.lintv
Terminal=false
Type=Application
Categories=Utility;AudioVideo;RemoteAccess;Network;
Keywords=TV;Android;Tailscale;Remote;scrcpy;ADB;
StartupNotify=true
StartupWMClass=io.github.theajmalrazaq.lintv
Actions=Stream;Status;

[Desktop Action Stream]
Name=Watch TV Screen
Exec=${BIN_DIR}/lintv --start

[Desktop Action Status]
Name=Check TV Status
Exec=${BIN_DIR}/lintv --status
EOF
chmod +x "${APP_DIR}/io.github.theajmalrazaq.lintv.desktop"
echo "[✓] Installed desktop launcher"

# 4. Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo ""
echo "Installation complete!"
echo "Run 'lintv' or find 'LinTV' in your application launcher."
