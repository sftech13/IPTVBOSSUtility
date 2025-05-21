#!/bin/bash
set -e

APP_NAME="IPTVBoss_Tool"
SOURCE_PY="src/iptv_gui_full.py"
ICON_FILE="assets/iptv_icon.png"
DISPLAY_NAME="IPTVBoss_Tool"
BUILD_DIR="iptvboss_tool_deb"
BIN_PATH="$BUILD_DIR/usr/local/bin"
DESKTOP_PATH="$BUILD_DIR/usr/share/applications"
ICON_DEST="$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"

cd "$(dirname "$0")/.."

# Sanity checks
[[ -f "$SOURCE_PY" ]] || {
    echo "❌ $SOURCE_PY missing"
    exit 1
}
[[ -f "$ICON_FILE" ]] || {
    echo "❌ $ICON_FILE missing"
    exit 1
}

echo "🧹 Cleaning…"
rm -rf build "$BUILD_DIR" *.spec dist
mkdir -p dist

echo "🛠 Building single Linux binary (with embedded .sh)…"
pyinstaller --noconfirm --onefile --windowed --clean \
    --hidden-import=tkinter \
    --add-data="$PWD/src/update.sh:." \
    --add-data="$PWD/src/linux_functions.sh:." \
    --name "$APP_NAME" \
    "$SOURCE_PY"

# Make sure binary exists
if [[ ! -f "dist/$APP_NAME" ]]; then
    echo "❌ PyInstaller build failed: dist/$APP_NAME not found"
    exit 1
fi

echo "📦 Staging .deb layout…"
mkdir -p "$BIN_PATH" "$DESKTOP_PATH" "$ICON_DEST"

# Install only the one-file binary
install -m 755 "dist/$APP_NAME" "$BIN_PATH/$DISPLAY_NAME"

# Icon
cp "$ICON_FILE" "$ICON_DEST/${APP_NAME}.png"

# .desktop
cat >"$DESKTOP_PATH/$DISPLAY_NAME.desktop" <<EOF
[Desktop Entry]
Name=IPTVBoss Utility Tool
Exec=/usr/local/bin/$DISPLAY_NAME
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Utility;Video;
EOF

# DEBIAN control
mkdir -p "$BUILD_DIR/DEBIAN"
cat >"$BUILD_DIR/DEBIAN/control" <<EOF
Package: IPTVBoss-Utility-Tool
Version: 1.0
Section: base
Priority: optional
Architecture: amd64
Maintainer: SFTech13
Depends: python3 (>= 3.8), python3-tk, ffmpeg
Description: IPTV BOSS Utility Tool & Stream Checker
 A tool to help with issues related to IPTV BOSS and a utility to check stream quality.
EOF

# postinst (no-op—dependencies are declared in control)
cat >"$BUILD_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/bash
# no-op: dependencies will be installed by the package manager
exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/postinst"

echo "📦 Building .deb…"
dpkg-deb --build "$BUILD_DIR"

# Move/rename .deb to dist/IPTVBoss_Tool.deb (always check the parent dir for the .deb)
DEB_OUT="$(dirname "$BUILD_DIR")/$(basename "$BUILD_DIR").deb"
if [[ ! -f "$DEB_OUT" ]]; then
    echo "❌ .deb package not found! Scanning for .deb files..."
    find . -name '*.deb'
    exit 1
fi

mv "$DEB_OUT" "dist/IPTVBoss_Tool.deb"

echo "✅ All-in-one DEB: dist/IPTVBoss_Tool.deb"
