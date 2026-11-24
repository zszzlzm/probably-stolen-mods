#!/usr/bin/env bash
# 构建 -> 部署到本地 Mods/GenerousBuyer -> 自检
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${GENEROUS_BUYER_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/GenerousBuyer"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/GenerousBuyer.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS/Localization"
# 游戏运行时只锁 DLL：先复制它，失败就整体放弃，不要留下半套文件。
if ! cp "$ROOT/build/GenerousBuyerMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: GenerousBuyerMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
cp "$ROOT/mod/Localization/"*.csv "$MODS/Localization/"
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/" 2>/dev/null || echo "warn: preview.png locked, skipped" >&2
fi

if [ ! -s "$MODS/GenerousBuyerMod.dll" ] || [ ! -s "$MODS/manifest.xml" ]; then
	echo "DEPLOY FAILED: dll or manifest missing" >&2
	exit 1
fi

LOC_COUNT=$(ls "$MODS/Localization/"*.csv 2>/dev/null | wc -l)
[ "$LOC_COUNT" -ge 2 ] || { echo "DEPLOY FAILED: expected 2 locale files, found $LOC_COUNT" >&2; exit 1; }

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/GenerousBuyerMod.dll") bytes"
echo "  localization: $LOC_COUNT file(s)"
