#!/usr/bin/env bash
# 打印一个"真的能用"的 Python 解释器路径（默认要求 Pillow + numpy）。
#
# 这台机器上 `python` / `python3` 是 Windows 应用商店的占位程序：什么都不做就退出 49，
# 所以 `command -v python3` 拿到的东西不可信。顺序：
#   $DSH_PYTHON -> DSH 运行时自带 -> python3 -> python
#
# 用法：PY="$(bash tools/find-python.sh)" || exit 1
#   或  PY="$(bash tools/find-python.sh "import PIL")"     # 只要求 Pillow
set -euo pipefail

REQUIRE="${1:-import PIL, numpy}"

CANDIDATES=()
[ -n "${DSH_PYTHON:-}" ] && CANDIDATES+=("$DSH_PYTHON")
CANDIDATES+=("${DSH_RUNTIME_PYTHON:-}")
CANDIDATES+=("C:/Users/$USERNAME/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe")
CANDIDATES+=("$(command -v python3 2>/dev/null || true)")
CANDIDATES+=("$(command -v python 2>/dev/null || true)")

for py in "${CANDIDATES[@]}"; do
	[ -n "$py" ] || continue
	[ -x "$py" ] || continue
	if "$py" -c "$REQUIRE" >/dev/null 2>&1; then
		echo "$py"
		exit 0
	fi
done

echo "ERROR: no usable Python (needs: $REQUIRE). Set DSH_PYTHON=/path/to/python" >&2
exit 1
