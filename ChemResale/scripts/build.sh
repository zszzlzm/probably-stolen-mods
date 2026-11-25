#!/usr/bin/env bash
# Build + deploy Reagent Resale (prototype A). Close the game first: the DLL is locked while it runs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${CHEM_RESALE_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ChemResale"

echo "== build =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/ChemResale.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4

echo "== deploy =="
mkdir -p "$MODS"
if ! cp "$ROOT/build/ChemResaleMod.dll" "$MODS/" 2>/dev/null; then
	echo "DEPLOY FAILED: ChemResaleMod.dll is locked (game still running?); nothing else was touched" >&2
	exit 1
fi
cp "$ROOT/mod/manifest.xml" "$MODS/"

echo "deployed -> $MODS"
echo "  dll: $(stat -c%s "$MODS/ChemResaleMod.dll") bytes"
