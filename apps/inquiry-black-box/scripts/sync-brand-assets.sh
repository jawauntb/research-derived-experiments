#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
SOURCE="${1:-"$ROOT/assets/brand/logo.png"}"
CANONICAL="$ROOT/assets/brand/logo.png"

if [[ ! -f "$SOURCE" ]]; then
  echo "Logo source not found: $SOURCE" >&2
  exit 1
fi

mkdir -p "$ROOT/assets/brand"
if [[ "$(cd "$(dirname "$SOURCE")" && pwd)/$(basename "$SOURCE")" != "$CANONICAL" ]]; then
  cp "$SOURCE" "$CANONICAL"
fi

DESKTOP_ASSETS="$ROOT/apps/desktop/assets"
EXTENSION_ASSETS="$ROOT/apps/extension/assets"
SITE_ASSETS="$REPO_ROOT/sites/inquiry_black_box/assets"

cp "$CANONICAL" "$DESKTOP_ASSETS/icon.png"
cp "$CANONICAL" "$SITE_ASSETS/aperture-mark.png"

sips -s format png -z 128 128 "$CANONICAL" --out "$SITE_ASSETS/aperture-icon.png" >/dev/null

for size in 16 32 48 128; do
  sips -s format png -z "$size" "$size" "$CANONICAL" --out "$EXTENSION_ASSETS/icon${size}.png" >/dev/null
done

ICONSET="$(mktemp -d "${TMPDIR:-/tmp}/inquiry-iconset.XXXXXX")/icon.iconset"
mkdir -p "$ICONSET"
sips -s format png -z 16 16 "$CANONICAL" --out "$ICONSET/icon_16x16.png" >/dev/null
sips -s format png -z 32 32 "$CANONICAL" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
sips -s format png -z 32 32 "$CANONICAL" --out "$ICONSET/icon_32x32.png" >/dev/null
sips -s format png -z 64 64 "$CANONICAL" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
sips -s format png -z 128 128 "$CANONICAL" --out "$ICONSET/icon_128x128.png" >/dev/null
sips -s format png -z 256 256 "$CANONICAL" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -s format png -z 256 256 "$CANONICAL" --out "$ICONSET/icon_256x256.png" >/dev/null
sips -s format png -z 512 512 "$CANONICAL" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -s format png -z 512 512 "$CANONICAL" --out "$ICONSET/icon_512x512.png" >/dev/null
sips -s format png -z 1024 1024 "$CANONICAL" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o "$DESKTOP_ASSETS/icon.icns"
