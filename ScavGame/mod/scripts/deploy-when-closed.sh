#!/usr/bin/env bash
# Wait for Probably Stolen to exit, then deploy the already-built mod payload.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${SCAV_ARCADE_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ScavArcade"
BUILD="$ROOT/build"

echo "waiting for game to exit..."
while tasklist 2>/dev/null | grep -qi "Probably Stolen.exe"; do
  sleep 3
done

mkdir -p "$MODS/Localization"
for i in $(seq 1 40); do
  if cp "$BUILD/ScavArcade.dll" "$MODS/" 2>/dev/null; then
    cp "$ROOT/manifest.xml" "$MODS/"
    rm -f "$MODS/Localization/"*.csv
    cp "$ROOT/Localization/"*.csv "$MODS/Localization/"
    echo "deployed after game exit"
    sha256sum "$MODS/ScavArcade.dll"
    exit 0
  fi
  sleep 3
done

echo "deploy failed: ScavArcade.dll still locked" >&2
exit 1
