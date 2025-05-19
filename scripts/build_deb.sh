#!/bin/bash
set -e

APP_NAME="iptv_gui_full"
SOURCE_PY="src/${APP_NAME}.py"
ICON_FILE="assets/iptv_icon.png"
DISPLAY_NAME="IPTV-BOSS-Utility"
BUILD_DIR="iptv_gui_deb"
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

echo "🛠 Building single Linux binary (with embedded .sh)…"
pyinstaller --noconfirm --onefile --windowed --clean \
    --hidden-import=tkinter \
    --add-data="$PWD/src/linux_functions.sh:." \
    "$SOURCE_PY"

echo "📦 Staging .deb layout…"
mkdir -p "$BIN_PATH" "$DESKTOP_PATH" "$ICON_DEST"

# Install only the one-file binary
install -m 755 "dist/$APP_NAME" "$BIN_PATH/$DISPLAY_NAME"

# Icon
cp "$ICON_FILE" "$ICON_DEST/${APP_NAME}.png"

# .desktop
cat >"$DESKTOP_PATH/$DISPLAY_NAME.desktop" <<EOF
[Desktop Entry]
Name=IPTV BOSS Maintenance Tool
Exec=/usr/local/bin/$DISPLAY_NAME
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Utility;Video;
EOF

# DEBIAN control
mkdir -p "$BUILD_DIR/DEBIAN"
cat >"$BUILD_DIR/DEBIAN/control" <<EOF
Package: IPTV-BOSS-Maintenance-Tool
Version: 1.0
Section: base
Priority: optional
Architecture: amd64
Maintainer: SFTech13
Depends: python3 (>= 3.8), python3-tk, ffmpeg
Description: IPTV BOSS Maintenance Tool & Stream Checker
 A tool to help wiht issues related to IPTV BOSS and a utility to check stream quality. 
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
mv "$BUILD_DIR.deb" "dist/BOSS_Utility.deb"

echo "✅ All-in-one DEB: dist/BOSS_Utility.deb"
