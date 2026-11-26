#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${SCAV_ARCADE_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ScavArcade"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/ScavArcade.csproj" -c Release -o "$ROOT/build" -t:Rebuild -v:minimal | tail -8

echo "== deploy =="
mkdir -p "$MODS/Localization"
if ! cp "$ROOT/build/ScavArcade.dll" "$MODS/" 2>/dev/null; then
  echo "DEPLOY FAILED: ScavArcade.dll is locked (game still running?)" >&2
  exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
rm -f "$MODS/Localization/"*.csv
cp "$ROOT/mod/Localization/"*.csv "$MODS/Localization/"
if [ -d "$ROOT/mod/Sounds" ]; then
  rm -rf "$MODS/Sounds"
  cp -r "$ROOT/mod/Sounds" "$MODS/Sounds"
fi

echo "deployed -> $MODS"
ls -la "$MODS" "$MODS/Localization"
