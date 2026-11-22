#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BALANCE="$ROOT/src/Balance.cs"

usage() {
  cat <<'TXT'
usage: scripts/set-balance.sh <key> <value>
  print-power            power drawn per printed cartridge (default 120)
  upgrade-cost           Wild Network unlock price (default 900)
  cartridge-durability   durability of a printed cartridge (default 900)
  cartridge-value        base value of a printed cartridge (default 120)
  filter-size            FILTER_SIZE_TAG written on printed cartridges (default 999)
TXT
}

resolve() {
  case "$1" in
    print-power) echo "PrintPowerCost" ;;
    upgrade-cost) echo "UpgradeCost" ;;
    cartridge-durability) echo "CartridgeDurability" ;;
    cartridge-value) echo "CartridgeValue" ;;
    filter-size) echo "CartridgeFilterSize" ;;
    *) return 1 ;;
  esac
}

if [ "$#" -ne 2 ]; then
  usage
  exit 1
fi
if ! KEY="$(resolve "$1")"; then
  echo "unknown balance key: $1"
  usage
  exit 1
fi
if ! [[ "$2" =~ ^[0-9]+$ ]]; then
  echo "value must be a non-negative integer, got: $2"
  exit 1
fi

sed -i -E "s/(${KEY} = )[0-9]+;/\1${2};/" "$BALANCE"
echo "Balance.${KEY} = ${2}"
"$ROOT/scripts/build.sh"
