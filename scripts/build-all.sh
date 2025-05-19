#!/bin/bash
set -e

echo "🔁 Running full build for .deb and .exe..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# === Build .deb ===
echo "📦 Starting .deb build..."
bash "$SCRIPT_DIR/build_deb.sh"

# === Build .exe ===
echo "💼 Starting Windows .exe build..."
bash "$SCRIPT_DIR/build-windows.sh"

# === Summary ===
echo ""
echo "✅ Build complete. Final artifacts:"
ls -lh "$ROOT_DIR/dist" | grep -E '\.deb$|\.exe$'

echo ""
echo "📁 Output folder: $ROOT_DIR/dist"
