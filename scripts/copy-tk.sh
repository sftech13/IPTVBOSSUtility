#!/bin/bash
set -e

PYWIN="$HOME/.wine/drive_c/Python38"

echo "🔍 Searching for Tcl/Tk on Ubuntu..."
TCL_PATH=$(find /usr/share -type d -name tcl* | grep -E 'tcl8\.[0-9]+' | head -n 1)
TK_PATH=$(find /usr/share -type d -name tk* | grep -E 'tk8\.[0-9]+' | head -n 1)

if [[ ! -d "$TCL_PATH" || ! -d "$TK_PATH" ]]; then
    echo "❌ Could not locate Tcl/Tk folders in /usr/share"
    exit 1
fi

echo "📂 Copying Tcl/Tk to Wine Python directory..."
mkdir -p "$PYWIN/tcl"
mkdir -p "$PYWIN/tk"

cp -r "$TCL_PATH" "$PYWIN/tcl/"
cp -r "$TK_PATH" "$PYWIN/tk/"

echo "✅ Tcl copied: $TCL_PATH"
echo "✅ Tk copied:  $TK_PATH"

# DLLs (for completeness, optional)
echo "📦 Copying dummy DLLs if needed (skip if already present)"
touch "$PYWIN/tcl86t.dll"
touch "$PYWIN/tk86t.dll"

echo "✅ Tcl/Tk resources injected into Wine Python"
