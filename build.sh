#!/usr/bin/env bash
# Build the JSON Form Viewer executable on Linux/Debian.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Installing dependencies ==="
python -m pip install -r requirements.txt

echo "=== Building executable ==="
python -m PyInstaller --clean --noconfirm JsonFormViewer.spec

echo
echo "=== Build complete ==="
echo "Executable: $(pwd)/dist/jsonviewer"
