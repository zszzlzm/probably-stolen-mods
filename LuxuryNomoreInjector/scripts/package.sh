#!/usr/bin/env bash
# 打发布包：构建 -> 组干净的模组文件夹 -> 校验 -> 压 zip -> 生成 steamcmd 上传用 .vdf
# 用法：bash scripts/package.sh
#   CHANGENOTE="..."   覆盖 vdf 里的更新说明
#   VIS_OVERRIDE=0     临时改可见性（0 公开 / 1 好友 / 2 隐藏）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/mod/manifest.xml"
DIST="$ROOT/dist"

VER="$(grep -o '<ModVersion>[^<]*' "$MANIFEST" | head -1 | sed 's/<ModVersion>//')"
MOD_ID="$(grep -o '<ID>[^<]*' "$MANIFEST" | head -1 | sed 's/<ID>//')"
if [ -z "$VER" ] || [ -z "$MOD_ID" ]; then
	echo "ERROR: cannot read ModVersion/ID from $MANIFEST" >&2
	exit 1
fi
PKG_NAME="LuxuryNomoreInjector-v$VER"
OUT="$DIST/$PKG_NAME"
DLL="LuxuryNomoreInjectorMod.dll"

echo "== build ($MOD_ID v$VER) =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/LuxuryNomoreInjector.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4
[ -s "$ROOT/build/$DLL" ] || { echo "ERROR: build produced no dll" >&2; exit 1; }

echo "== preview =="
# 需要 Python 3 + Pillow；不要用 Windows 应用商店的占位 python（它什么都不做）
PY="$(bash "$ROOT/../tools/find-python.sh" "import PIL, numpy")" || exit 1
export PYTHONIOENCODING=utf-8
# 默认输入就是实际用的那张关键图（keyart_shift2），默认缩放/偏移不改变既有构图。
"$PY" "$ROOT/scripts/make_cover.py" || { echo "ERROR: preview generation failed" >&2; exit 1; }

echo "== assemble =="
SMALL_PREVIEW="$ROOT/build/preview_640.png"
[ -s "$SMALL_PREVIEW" ] || { echo "ERROR: $SMALL_PREVIEW missing" >&2; exit 1; }
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$ROOT/build/$DLL" "$OUT/"
cp "$MANIFEST" "$OUT/"
# 包内放 640x360 的小图：工坊 file_size 只统计 contentfolder
cp "$SMALL_PREVIEW" "$OUT/preview.png"
cp "$ROOT/packaging/README.txt" "$OUT/"
if [ -d "$ROOT/mod/Localization" ]; then
	mkdir -p "$OUT/Localization"
	cp "$ROOT/mod/Localization/"*.csv "$OUT/Localization/"
fi

echo "== verify =="
fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }

[ -s "$OUT/manifest.xml" ] || fail "manifest.xml missing"
[ -s "$OUT/$DLL" ] || fail "dll missing"
[ -s "$OUT/preview.png" ] || fail "preview.png missing"
PREVIEW_SIZE=$(stat -c%s "$OUT/preview.png")
[ "$PREVIEW_SIZE" -lt 1048576 ] || fail "preview.png is larger than 1 MB ($PREVIEW_SIZE bytes)"
# 包内必须是 640x360 的小图，1280 全画质只作为工坊 previewfile（不进包）
PREVIEW_DIMS=$("$PY" -c "import sys; from PIL import Image; print('%dx%d' % Image.open(sys.argv[1]).size)" "$OUT/preview.png")
[ "$PREVIEW_DIMS" = "640x360" ] || fail "in-package preview.png should be 640x360, got $PREVIEW_DIMS"

grep -q "<Assembly>$DLL</Assembly>" "$OUT/manifest.xml" || fail "manifest does not list the dll"
grep -q "<Capabilities" "$OUT/manifest.xml" || fail "manifest has no <Capabilities> element"

# 设置项靠 Localization/*.csv 提供名字与说明：少了就只有 "config.multiplier" 原始 key
LOC_COUNT=$(ls "$OUT/Localization/"*.csv 2>/dev/null | wc -l)
[ "$LOC_COUNT" -ge 2 ] || fail "expected at least 2 localization files, found $LOC_COUNT"
for f in "$OUT/Localization/"*.csv; do
	[ -s "$f" ] || fail "$(basename "$f") is empty"
	grep -q "^config.multiplier," "$f" || fail "$(basename "$f") lacks the config.multiplier key"
done

# 模组扫描器会拒绝的载荷：可执行文件、脚本、未知 DLL、压缩包、美术源文件
BAD=$(find "$OUT" -type f \( -iname '*.exe' -o -iname '*.bat' -o -iname '*.cmd' -o -iname '*.ps1' \
	-o -iname '*.js' -o -iname '*.vbs' -o -iname '*.lnk' -o -iname '*.zip' -o -iname '*.7z' \
	-o -iname '*.rar' -o -iname '*.psd' -o -iname '*.aseprite' -o -iname '*.pdb' -o -iname '*.cs' \
	-o \( -iname '*.dll' ! -iname "$DLL" \) \) -print)
[ -z "$BAD" ] || fail "forbidden files in package: $BAD"

echo "  dll          $(stat -c%s "$OUT/$DLL") bytes"
echo "  preview.png  $PREVIEW_SIZE bytes"
echo "  files        $(find "$OUT" -type f | wc -l)"

echo "== zip =="
ZIP="$DIST/$PKG_NAME.zip"
rm -f "$ZIP"
# cygpath -m 给出 C:/... 形式，VDF 里的路径不需要转义反斜杠
WIN_OUT="$(cygpath -m "$OUT" 2>/dev/null || echo "$OUT")"
bash "$ROOT/../tools/make_zip.sh" "$ZIP" "$OUT"
[ -s "$ZIP" ] || fail "zip was not created"
echo "  $ZIP ($(stat -c%s "$ZIP") bytes)"

echo "== checksums =="
{
	echo "# $PKG_NAME"
	( cd "$OUT" && find . -type f | sed 's|^\./||' | sort | while read -r f; do
		printf '%s  %s\n' "$(sha256sum "$f" | cut -d' ' -f1)" "$f"
	done )
	echo ""
	printf '%s  %s\n' "$(sha256sum "$ZIP" | cut -d' ' -f1)" "$(basename "$ZIP")"
} > "$DIST/SHA256SUMS.txt"
cat "$DIST/SHA256SUMS.txt"

echo "== steamcmd vdf =="
VDF="$DIST/${MOD_ID}.vdf"
WIN_PREVIEW="$(cygpath -m "$ROOT/mod/preview.png" 2>/dev/null || echo "$ROOT/mod/preview.png")"
# 已上传过的条目：沿用原 publishedfileid / visibility，否则会新建重复条目或把公开条目改回隐藏。
PUB_ID="0"
VIS="2"
if [ -f "$VDF" ]; then
	PREV_ID="$(grep -oE '"publishedfileid"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_ID:-}" ] && PUB_ID="$PREV_ID"
	PREV_VIS="$(grep -oE '"visibility"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_VIS:-}" ] && VIS="$PREV_VIS"
fi
VIS="${VIS_OVERRIDE:-$VIS}"
CHANGENOTE="${CHANGENOTE:-v$VER 首次发布。}"

# 工坊长描述由本文件提供（1.1.0 起）。以前这里写死一句短描述，每次上传都会把页面上的长描述冲掉。
# 坑：KeyValues 没有转义，值里的 ASCII 双引号会提前截断字符串、整份 vdf 解析失败 —— 源文件只许用「」。
DESC_FILE="$ROOT/packaging/workshop_description.txt"
[ -s "$DESC_FILE" ] || { echo "ERROR: $DESC_FILE missing" >&2; exit 1; }
DESC_ESC="$("$PY" -c '
import sys
t = open(sys.argv[1], encoding="utf-8").read().rstrip()
bad = [i + 1 for i, l in enumerate(t.split("\n")) if chr(34) in l]
if bad:
    sys.stderr.write("ERROR: ASCII double quote in %s at line(s) %s; "
                     "KeyValues cannot escape it, use 「」 instead\n"
                     % (sys.argv[1], ", ".join(map(str, bad))))
    raise SystemExit(1)
# Steam 的工坊描述上限按字节算（约 8000）。超了 SteamCMD 只在最后一步报
# "Failed to update workshop item (Invalid Parameter)"，而且这时内容已经传上去了。
size = len(t.encode("utf-8"))
if size > 7900:
    sys.stderr.write("ERROR: %s is %d UTF-8 bytes; Steam rejects descriptions over 8000 "
                     "(trim it, about 2600 Chinese characters)\n" % (sys.argv[1], size))
    raise SystemExit(1)
sys.stderr.write("  description  %d bytes\n" % size)
sys.stdout.write(t)
' "$DESC_FILE")" || exit 1

cat > "$VDF" <<EOF
"workshopitem"
{
	"appid"			"4348910"
	"publishedfileid"	"$PUB_ID"
	"contentfolder"		"$WIN_OUT"
	"previewfile"		"$WIN_PREVIEW"
	"visibility"		"$VIS"
	"title"			"更好的奥克莫吸注射器 / Luxury Nomore Injector"
	"description"		"$DESC_ESC"
	"changenote"		"$CHANGENOTE"
}
EOF
cp "$ROOT/packaging/workshop_description.txt" "$DIST/workshop_description.txt"
echo "  $VDF (publishedfileid=$PUB_ID visibility=$VIS)"
echo ""
echo "package ready:"
echo "  folder : $OUT"
echo "  zip    : $ZIP"
echo "  vdf    : $VDF"
