#!/usr/bin/env bash
# 兼容旧调用：真正的解析逻辑在仓库根 tools/find-python.sh。
# 保留这个壳是因为文档和 skill 里已经写了 ChemResale/scripts/find-python.sh。
set -euo pipefail
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/tools/find-python.sh" "$@"
