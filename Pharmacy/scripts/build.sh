#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${PHARMACY_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/Pharmacy"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/Pharmacy.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS/Localization"
# 顺序很重要：先把唯一会被游戏锁住的 DLL 复制完，再动其他文件。
# 否则 DLL 复制失败时，已经被删掉的语言包不会被补回来（曾经因此整屏英文）。
if ! cp "$ROOT/build/PharmacyMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: PharmacyMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"

# 物品美术（16x16 像素画）
rm -rf "$MODS/Textures"
if [ -d "$ROOT/mod/Textures" ]; then
	cp -r "$ROOT/mod/Textures" "$MODS/Textures"
fi

rm -f "$MODS/Localization/"*.csv
cp "$ROOT/mod/Localization/"*.csv "$MODS/Localization/"
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/"
fi

LOC_COUNT=0
for f in "$ROOT/mod/Localization/"*.csv; do
	base="$(basename "$f")"
	if [ ! -s "$MODS/Localization/$base" ]; then
		echo "DEPLOY FAILED: $base is missing or empty in $MODS/Localization" >&2
		exit 1
	fi
	LOC_COUNT=$((LOC_COUNT + 1))
done
[ "$LOC_COUNT" -ge 2 ] || { echo "DEPLOY FAILED: expected 2 localization files, found $LOC_COUNT" >&2; exit 1; }
[ -s "$MODS/PharmacyMod.dll" ] || { echo "DEPLOY FAILED: dll missing" >&2; exit 1; }

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/PharmacyMod.dll") bytes"
echo "  localization: $LOC_COUNT file(s), $(cat "$MODS/Localization/"*.csv | grep -c .) line(s)"
for spr in calm_agent painkiller_pill; do
	p="$MODS/Textures/Items/$spr.png"
	[ -s "$p" ] || { echo "DEPLOY FAILED: sprite $spr missing" >&2; exit 1; }
	echo "  sprite: $spr.png $(stat -c%s "$p") bytes"
done
