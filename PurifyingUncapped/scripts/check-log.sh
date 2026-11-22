#!/usr/bin/env bash
# 启动游戏、在 Mod 菜单里启用「净化无上限」后运行本脚本，
# 确认 ModLoader 真的加载了 DLL、Harmony 打上了补丁、mod 完成了初始化。
set -uo pipefail

LOG="${PURIFYING_UNCAPPED_LOG:-${USERPROFILE:-/c/Users/$USER}/AppData/LocalLow/Questing Goose Studio/Probably Stolen/Player.log}"

if [ ! -f "$LOG" ]; then
	echo "找不到 Player.log：$LOG" >&2
	exit 1
fi

echo "log: $LOG"
echo

line=$(grep -n "Loading: PurifyingUncappedMod.dll" "$LOG" | tail -1 | cut -d: -f1)
if [ -z "${line:-}" ]; then
	echo "没有找到 PurifyingUncapped 的加载记录。" >&2
	echo "检查：游戏是否在部署后重启过？mod 是否已在 Mod 菜单里启用/审核通过？" >&2
	exit 2
fi

echo "== ModLoader 记录 =="
sed -n "${line},$((line + 2))p" "$LOG"

echo
echo "== mod 自身日志 =="
grep -n "Initialized: Purifying per-night removal cap" "$LOG" | tail -1 || echo "（没有找到初始化日志）"

patched=$(sed -n "$((line + 1))p" "$LOG" | grep -oE "Harmony: [0-9]+" | grep -oE "[0-9]+" | head -1)
echo
if [ "${patched:-0}" -ge 1 ]; then
	echo "OK: PurifyingShare 补丁已应用（Harmony: ${patched} method(s) patched）"
	exit 0
fi

echo "警告：DLL 已加载但没有打上补丁（Harmony: ${patched:-0}）" >&2
exit 3
