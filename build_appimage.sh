#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"

cd "$ROOT"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python executable not found: $PYTHON" >&2
    exit 1
fi
if ! command -v "$APPIMAGETOOL" >/dev/null 2>&1 && [[ ! -x "$APPIMAGETOOL" ]]; then
    echo "appimagetool not found; install it or set APPIMAGETOOL=/path/to/appimagetool" >&2
    exit 1
fi
"$PYTHON" -c 'import tkinter, PIL, PyInstaller' || {
    echo "Install the build requirements and the system python3-tk package first." >&2
    exit 1
}

"$PYTHON" -m PyInstaller --noconfirm --clean Packager.spec

APP_VERSION="$("$PYTHON" -c 'import sys; sys.path.insert(0, "src"); import engine; print(engine.VERSION)')"
APPDIR="$ROOT/local-linux-build/AppDir"
OUTPUT="$ROOT/dist/NSP-Box-${APP_VERSION}-x86_64.AppImage"
rm -rf -- "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp -- "$ROOT/dist/NSP-Box" "$APPDIR/usr/bin/NSP-Box"
mkdir -p "$APPDIR/usr/share/doc/nsp-box/licenses"
cp -- "$ROOT/README.md" "$ROOT/LICENSE.txt" "$ROOT/THIRD_PARTY_NOTICES.md" "$ROOT/DISCLAIMER.md" "$APPDIR/usr/share/doc/nsp-box/"
cp -- "$ROOT/licenses/"* "$APPDIR/usr/share/doc/nsp-box/licenses/"

cat >"$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE="$(dirname -- "$(readlink -f -- "$0")")"
exec "$HERE/usr/bin/NSP-Box" "$@"
APPRUN
chmod +x "$APPDIR/AppRun" "$APPDIR/usr/bin/NSP-Box"

cat >"$APPDIR/NSP-Box.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NSP Box
Comment=Package extracted game snapshots into NSP files
Exec=NSP-Box
Icon=NSP-Box
Categories=Utility;
Terminal=false
StartupNotify=true
DESKTOP

"$PYTHON" - "$ROOT/app.ico" "$APPDIR/NSP-Box.png" <<'PYTHON'
import sys
from PIL import Image

with Image.open(sys.argv[1]) as icon:
    icon.seek(0)
    icon.convert("RGBA").resize((256, 256), Image.Resampling.LANCZOS).save(sys.argv[2])
PYTHON

mkdir -p "$ROOT/dist"
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod +x "$OUTPUT"
printf 'Created %s\n' "$OUTPUT"
