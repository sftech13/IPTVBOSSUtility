#!/bin/bash
set -e

INSTALLER="python-installer.exe"
WINE_PYDIR='C:\users\sftech13\Local Settings\Application Data\Programs\Python\Python38'
WINE_PYEXE="$WINE_PYDIR\\python.exe"
LINUX_PYEXE="$HOME/.wine/drive_c/users/sftech13/Local Settings/Application Data/Programs/Python/Python38/python.exe"
SCRIPT_NAME="src/iptv_gui_full.py"
ICON_NAME="assets/iptv_icon.ico"

echo "📂 Checking for Wine-Python at: $LINUX_PYEXE"
if [[ ! -f "$LINUX_PYEXE" ]]; then
    echo "❌ Python not found — launching installer via Wine"
    cd ~/Downloads
    [[ -f "$INSTALLER" ]] || {
        echo "❌ $INSTALLER missing"
        exit 1
    }
    wine "$INSTALLER"
fi

echo "✅ Installing dependencies under Wine…"
wine "$WINE_PYEXE" -m pip install --upgrade pip pyinstaller

echo "📦 Building single EXE (with embedded .bat)…"
cd "$(dirname "$0")/.."
wine "$WINE_PYEXE" -m PyInstaller \
    --noconfirm \
    --onefile \
    --windowed \
    --icon="$ICON_NAME" \
    --add-data "src/IPTVBossMaintenanceUtility.bat;." \
    "$SCRIPT_NAME"

# verify
EXE="dist/iptv_gui_full.exe"
if [[ -f "$EXE" ]]; then
    echo "✅ EXE built: $EXE"
    echo "🎉 All-in-one! .bat is embedded in the EXE—no external files needed."
else
    echo "❌ Build failed: $EXE missing" >&2
    exit 1
fi
