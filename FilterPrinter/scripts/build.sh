#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${FILTER_PRINTER_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/FilterPrinter"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/FilterPrinter.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS/Localization"
# 先复制唯一会被游戏锁住的 DLL：失败就整体放弃，不要先删语言包。
if ! cp "$ROOT/build/FilterPrinterMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: FilterPrinterMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
rm -f "$MODS/Localization/"*.csv
cp "$ROOT/mod/Localization/"*.csv "$MODS/Localization/"
if [ -d "$ROOT/mod/Textures" ]; then
	mkdir -p "$MODS/Textures/Items"
	rm -f "$MODS/Textures/Items/"*.png
	cp "$ROOT/mod/Textures/Items/"*.png "$MODS/Textures/Items/"
fi
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/"
fi

# 部署后自检：本地化文件缺失时直接失败，避免再出现「整屏英文 + 原始 key」
LOC_COUNT=0
for f in "$ROOT/mod/Localization/"*.csv; do
	base="$(basename "$f")"
	if [ ! -s "$MODS/Localization/$base" ]; then
		echo "DEPLOY FAILED: $base is missing or empty in $MODS/Localization" >&2
		exit 1
	fi
	LOC_COUNT=$((LOC_COUNT + 1))
done
if [ "$LOC_COUNT" -lt 2 ]; then
	echo "DEPLOY FAILED: expected at least 2 localization files, found $LOC_COUNT" >&2
	exit 1
fi
LOC_LINES=$(cat "$MODS/Localization/"*.csv | grep -c .)
if [ ! -s "$MODS/FilterPrinterMod.dll" ] || [ ! -s "$MODS/manifest.xml" ]; then
	echo "DEPLOY FAILED: dll or manifest missing" >&2
	exit 1
fi
if [ -d "$ROOT/mod/Textures/Items" ]; then
	[ -s "$MODS/Textures/Items/fp_printer.png" ] || {
		echo "DEPLOY FAILED: Textures/Items/fp_printer.png missing in $MODS" >&2
		exit 1
	}
fi

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/FilterPrinterMod.dll") bytes"
echo "  localization: $LOC_COUNT file(s), $LOC_LINES line(s)"
