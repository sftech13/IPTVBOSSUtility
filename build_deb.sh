#!/bin/bash
set -e

APP_NAME="iptv_gui_full"
DISPLAY_NAME="IPTV-Stream-Checker"
SOURCE_PY="${APP_NAME}.py"
BUILD_DIR="iptv_gui_deb"
BIN_PATH="$BUILD_DIR/usr/local/bin"
ICON_NAME="iptv_gui"
ICON_FILE="iptv_icon.png"
DESKTOP_FILE="$BUILD_DIR/usr/share/applications/${ICON_NAME}.desktop"
ICON_DEST="$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"

cd "$(dirname "$0")"

if [[ ! -f "$SOURCE_PY" ]]; then
    echo "❌ Source file '$SOURCE_PY' not found"
    exit 1
fi

if [[ ! -f "$ICON_FILE" ]]; then
    echo "❌ Icon file '$ICON_FILE' not found"
    exit 1
fi

echo "🧹 Cleaning previous builds..."
rm -rf build dist "$BUILD_DIR" *.spec

echo "🛠 Building PyInstaller binary..."
pyinstaller --noconfirm --onefile --windowed --clean --hidden-import=tkinter "$SOURCE_PY"

echo "📦 Creating .deb directory structure..."
mkdir -p "$BIN_PATH" "$ICON_DEST" "$(dirname "$DESKTOP_FILE")"

echo "📦 Copying binary..."
# Make it portable with staticx
echo "📦 Creating statically linked binary with staticx..."
staticx "dist/$APP_NAME" "dist/${APP_NAME}_static"

# Copy the portable binary into the package
cp "dist/${APP_NAME}_static" "$BIN_PATH/$DISPLAY_NAME"
chmod +x "$BIN_PATH/$DISPLAY_NAME"

echo "🖼 Installing icon..."
cp "$ICON_FILE" "$ICON_DEST/${ICON_NAME}.png"

echo "🖥 Creating desktop shortcut..."
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
Depends: python3 (>= 3.8), python3-tk, ffmpeg
Description: IPTV Stream Quality Checker
 A simple IPTV checking tool with GUI for .m3u playlists.
EOF

echo "📜 Adding postinst script..."
cat <<'EOF' >"$BUILD_DIR/DEBIAN/postinst"
#!/bin/bash
set -e
echo "🔧 Ensuring required dependencies are present..."
apt-get update
apt-get install -y python3 python3-tk ffmpeg
exit 0
EOF
chmod +x "$BUILD_DIR/DEBIAN/postinst"

echo "📦 Building .deb package..."
dpkg-deb --build "$BUILD_DIR"

VERSION_TAG="${GITHUB_REF_NAME:-1.0}"
FINAL_NAME="iptv_gui_v${VERSION_TAG}.deb"
mv "${BUILD_DIR}.deb" "$FINAL_NAME"

echo "✅ Done! Build Summary:"
echo " - Binary:     dist/$APP_NAME"
echo " - Debian pkg: $FINAL_NAME"
