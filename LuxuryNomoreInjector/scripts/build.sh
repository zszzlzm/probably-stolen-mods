#!/usr/bin/env bash
# 构建 -> 部署到本地 Mods/LuxuryNomoreInjector -> 自检
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${LUXURY_INJECTOR_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/LuxuryNomoreInjector"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/LuxuryNomoreInjector.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS"
# 游戏运行时只锁 DLL：先复制它，失败就整体放弃，不要留下半套文件。
if ! cp "$ROOT/build/LuxuryNomoreInjectorMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: LuxuryNomoreInjectorMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
# 游戏内模组列表的缩略图读的是 Mods/<文件夹>/preview.png。
# 注意：新增文件会改变 folderHash，跑完要重签本地信任（见文末提示）。
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/" 2>/dev/null || echo "warn: preview.png locked, skipped" >&2
fi

if [ ! -s "$MODS/LuxuryNomoreInjectorMod.dll" ] || [ ! -s "$MODS/manifest.xml" ]; then
	echo "DEPLOY FAILED: dll or manifest missing" >&2
	exit 1
fi

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/LuxuryNomoreInjectorMod.dll") bytes"
if [ -f "$MODS/preview.png" ]; then
	echo "  preview: $(stat -c%s "$MODS/preview.png") bytes"
	echo "  note: 文件集变了就重签一次信任："
	echo "        python tools/trust_local.py --folder \"$MODS\" --id harness.luxury-nomore-injector --dll LuxuryNomoreInjectorMod.dll"
fi
