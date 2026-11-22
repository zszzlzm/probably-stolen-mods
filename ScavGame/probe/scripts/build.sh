#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${SCAV_PROBE_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ScavProbe"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/ScavProbe.csproj" -c Release -o "$ROOT/build" -t:Rebuild -v:minimal | tail -8

echo "== deploy =="
mkdir -p "$MODS/Sounds"
if ! cp "$ROOT/build/ScavProbe.dll" "$MODS/" 2>/dev/null; then
  echo "DEPLOY FAILED: ScavProbe.dll is locked (game still running?)" >&2
  exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"
cp "$ROOT/mod/Sounds/probe_beep.wav" "$MODS/Sounds/"

echo "deployed -> $MODS"
ls -la "$MODS"
