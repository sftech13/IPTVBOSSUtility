#!/bin/bash

set -e # Exit on error

# === CONFIG ===
APP_NAME="iptv_gui_full"
DISPLAY_NAME="IPTV-Stream-Checker"
SOURCE_PY="${APP_NAME}.py"
BUILD_DIR="iptv_gui_deb"
BIN_PATH="$BUILD_DIR/usr/local/bin"
ICON_NAME="iptv_gui"
ICON_FILE="iptv_icon.png"
DESKTOP_FILE="$BUILD_DIR/usr/share/applications/${ICON_NAME}.desktop"
ICON_DEST="$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"

# === VALIDATION ===
cd "$(dirname "$0")"

[[ -f "$SOURCE_PY" ]] || {
    echo "❌ Source file '$SOURCE_PY' not found"
    exit 1
}

[[ -f "$ICON_FILE" ]] || {
    echo "❌ Icon file '$ICON_FILE' not found"
    exit 1
}

echo "🧹 Cleaning build folders..."
rm -rf build dist "$BUILD_DIR" *.spec

# === BUILD EXECUTABLE ===
echo "🛠 Building standalone binary with PyInstaller..."
pyinstaller --onefile --windowed --clean --hidden-import=tkinter "$SOURCE_PY"

# === Package Setup ===
echo "📦 Setting up .deb structure..."
mkdir -p "$BIN_PATH" "$ICON_DEST" "$(dirname "$DESKTOP_FILE")"

echo "📦 Copying built binary..."
cp "dist/$APP_NAME" "$BIN_PATH/$DISPLAY_NAME"
chmod +x "$BIN_PATH/$DISPLAY_NAME"

echo "🖼 Copying icon..."
cp "$ICON_FILE" "$ICON_DEST/${ICON_NAME}.png"

echo "🖥 Creating desktop entry..."
cat <<EOF >"$DESKTOP_FILE"
[Desktop Entry]
Name=IPTV Stream Checker
Exec=/usr/local/bin/$DISPLAY_NAME
Icon=${ICON_NAME}
Terminal=false
Type=Application
Categories=Utility;Video;
EOF

echo "📋 Writing DEBIAN control file..."
mkdir -p "$BUILD_DIR/DEBIAN"
cat <<EOF >"$BUILD_DIR/DEBIAN/control"
Package: iptv-stream-checker
Version: 1.0
Section: base
Priority: optional
Architecture: amd64
Maintainer: SFTech13
Description: IPTV Stream Quality Checker
 A simple IPTV checking tool with GUI for .m3u playlists.
EOF

echo "📦 Building .deb package..."
dpkg-deb --build "$BUILD_DIR"

echo "✅ Done! Built:"
echo " - Binary:     dist/$APP_NAME"
echo " - Debian pkg: $BUILD_DIR.deb"
