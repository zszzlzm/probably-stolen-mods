#!/usr/bin/env bash
# 打发布 zip：make_zip.sh <out.zip> <source-dir>
#
# 产物结构与以前的 `Compress-Archive -Path <dir>` 一致：顶层带目录名，
# 例如 `FilterPrinter-v1.1.1/FilterPrinterMod.dll`。
#
# 为什么不用 PowerShell：`Compress-Archive` 在 PowerShell 5.1 里是自动加载模块，
# 如果父进程（git-bash / pwsh 7）把 PS7 的 PSModulePath 传下来，5.1 会报
# 「command was found in the module 'Microsoft.PowerShell.Archive', but the module
# could not be loaded」——同一个脚本在普通终端里却没事，属于环境相关的偶发失败。
# python 的 shutil.make_archive 是标准库，结果稳定，且 package.sh 本来就需要 python。
set -euo pipefail

OUT="${1:?usage: make_zip.sh <out.zip> <source-dir>}"
SRC="${2:?usage: make_zip.sh <out.zip> <source-dir>}"

[ -d "$SRC" ] || { echo "make_zip: no such directory: $SRC" >&2; exit 1; }

PY="$(bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/find-python.sh" "import zipfile")" || exit 1
export PYTHONIOENCODING=utf-8

"$PY" - "$OUT" "$SRC" <<'PYEOF'
import os
import shutil
import sys

out, src = sys.argv[1], sys.argv[2]
src = os.path.abspath(src)
parent, name = os.path.dirname(src), os.path.basename(src)
base = out[:-4] if out.lower().endswith(".zip") else out
produced = shutil.make_archive(base, "zip", parent, name)   # 顶层带目录名
print(produced)
PYEOF

[ -s "$OUT" ] || { echo "make_zip: archive was not created: $OUT" >&2; exit 1; }
