#!/usr/bin/env bash
# Build + deploy Purifying Uncapped. Close the game first: the DLL is locked while it runs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${PURIFYING_UNCAPPED_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/PurifyingUncapped"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/PurifyingUncapped.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS"
if ! cp "$ROOT/build/PurifyingUncappedMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: PurifyingUncappedMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
if [ -f "$ROOT/mod/preview.png" ]; then
	cp "$ROOT/mod/preview.png" "$MODS/"
fi

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/PurifyingUncappedMod.dll") bytes"
