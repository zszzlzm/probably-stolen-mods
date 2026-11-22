#!/usr/bin/env bash
# Wait for the game to exit, then build + deploy (Windows locks the DLL while the game runs).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXE_NAME="Probably Stolen.exe"

echo "waiting for $EXE_NAME to exit..."
for _ in $(seq 1 720); do
	if ! tasklist 2>/dev/null | grep -qiF "$EXE_NAME"; then
		echo "game exited; deploying"
		break
	fi
	sleep 5
done

if tasklist 2>/dev/null | grep -qiF "$EXE_NAME"; then
	echo "TIMEOUT: game still running after 60 minutes; not deployed" >&2
	exit 1
fi

for attempt in $(seq 1 60); do
	if bash "$ROOT/scripts/build.sh"; then
		echo "deployed on attempt $attempt"
		exit 0
	fi
	echo "deploy attempt $attempt failed (dll still locked?); retrying in 5s"
	sleep 5
done
echo "GAVE UP: could not deploy" >&2
exit 1
