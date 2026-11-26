#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GAME="${SCAV_ARCADE_GAME_DIR:-/f/SteamLibrary/steamapps/common/Probably Stolen}"
MODS="$GAME/Mods/ScavArcade"
SAVE_DIR="${PS_SAVE_DIR:-$HOME/AppData/LocalLow/Questing Goose Studio/Probably Stolen}"
DATA="$SAVE_DIR/ModData/harness_scav-arcade"
FLAG="$DATA/autotest.flag"
REPORT="$DATA/autotest-report.txt"
LOG="$SAVE_DIR/Player.log"

if tasklist 2>/dev/null | grep -qi "Probably Stolen"; then
  echo "游戏还在运行。先关掉游戏，否则 DLL 会被锁。" >&2
  exit 1
fi

echo "== build/deploy =="
bash "$ROOT/scripts/build.sh"

rm -f "$REPORT" "$FLAG" "$MODS/autotest.flag"
mkdir -p "$DATA"
printf 'scav-arcade-autotest\n' > "$FLAG"
echo "flag: $FLAG"

echo "== launch =="
powershell.exe -NoProfile -Command "Start-Process 'F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen.exe'" >/dev/null 2>&1 || true

echo "等待 autotest-report.txt。"
echo "需要你进游戏，读档并走到垃圾场；进入地点后自检会自动跑。"
for _ in $(seq 1 180); do
  if [ -f "$REPORT" ]; then
    echo
    echo "== report =="
    cat "$REPORT"
    exit 0
  fi
  sleep 2
done

echo "超时：没等到报告。" >&2
if [ -f "$LOG" ]; then
  echo "== Player.log tail ==" >&2
  tail -40 "$LOG" >&2
fi
exit 1
