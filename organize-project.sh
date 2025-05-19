#!/bin/bash
set -e

echo "🧹 Organizing IPTVQuality project structure..."

# === Create folders ===
mkdir -p src assets scripts packaging

# === Move source code ===
mv iptv_gui_full.py iptv_checker_core.py requirements.txt src/ 2>/dev/null || true

# === Move assets ===
mv iptv_icon.* assets/ 2>/dev/null || true

# === Move scripts ===
mv build_deb.sh build-windows.sh copy-tk.sh python-installer.exe scripts/ 2>/dev/null || true

# === Move spec/wxs/version related files ===
mv iptv_gui_full.spec installer.wxs version.txt packaging/ 2>/dev/null || true

# === Ensure dist folder exists ===
mkdir -p dist

# === Suggest deletion of unused folders ===
if [[ -d "pyinstaller" ]]; then
    echo "⚠️  'pyinstaller/' exists — you can delete it if you're done with custom bootloaders."
fi

if [[ -d "pyi_embed" ]]; then
    echo "⚠️  'pyi_embed/' exists — you can delete it if you're no longer using embeddable Python."
fi

echo "✅ Done. Your project is now organized!"
