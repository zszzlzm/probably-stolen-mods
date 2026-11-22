#!/usr/bin/env bash
# 构建 -> 部署到本地 Mods/ReductionFern -> 自检
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${REDUCTION_FERN_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ReductionFern"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/ReductionFern.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS/Localization" "$MODS/Textures/Items"
# 游戏运行时只锁 DLL：先复制它，失败就整体放弃，不要留下半套文件。
if ! cp "$ROOT/build/ReductionFernMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: ReductionFernMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
rm -f "$MODS/Localization/"*.csv
cp "$ROOT/mod/Localization/"*.csv "$MODS/Localization/"
rm -f "$MODS/Textures/Items/"*.png
cp "$ROOT/mod/Textures/Items/"*.png "$MODS/Textures/Items/"
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/"
fi

# 部署后自检：缺语言包或缺精灵都会让游戏里出现裸 key / unknown 图
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

SPRITE_NAMES="restoring_fern_seed restoring_fern_s restoring_fern restoring_fern_l restoring_fern_p"
SPRITE_COUNT=0
for name in $SPRITE_NAMES; do
	if [ ! -s "$MODS/Textures/Items/$name.png" ]; then
		echo "DEPLOY FAILED: missing sprite $name.png" >&2
		exit 1
	fi
	SPRITE_COUNT=$((SPRITE_COUNT + 1))
done

if [ ! -s "$MODS/ReductionFernMod.dll" ] || [ ! -s "$MODS/manifest.xml" ]; then
	echo "DEPLOY FAILED: dll or manifest missing" >&2
	exit 1
fi

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/ReductionFernMod.dll") bytes"
echo "  localization: $LOC_COUNT file(s)"
echo "  sprites: $SPRITE_COUNT"
