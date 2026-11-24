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
PKG_NAME="GenerousBuyer-v$VER"
OUT="$DIST/$PKG_NAME"
DLL="GenerousBuyerMod.dll"

echo "== build ($MOD_ID v$VER) =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/GenerousBuyer.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4
[ -s "$ROOT/build/$DLL" ] || { echo "ERROR: build produced no dll" >&2; exit 1; }

echo "== preview =="
# 需要 Python 3 + Pillow；不要用 Windows 应用商店的占位 python（它什么都不做）
PY="${DSH_PYTHON:-$(command -v python3 || command -v python || true)}"
if [ -z "$PY" ] || ! "$PY" -c "import PIL" >/dev/null 2>&1; then
	echo "ERROR: need Python 3 with Pillow; set DSH_PYTHON=/path/to/python" >&2
	exit 1
fi
KEYART="$ROOT/refs/gen/keyart.png"
if [ -f "$KEYART" ]; then
	"$PY" "$ROOT/scripts/make_cover.py" "$KEYART" || { echo "ERROR: preview generation failed" >&2; exit 1; }
elif [ ! -s "$ROOT/mod/preview.png" ]; then
	echo "ERROR: no key art and no mod/preview.png" >&2
	exit 1
fi

echo "== assemble =="
SMALL_PREVIEW="$ROOT/build/preview_640.png"
[ -s "$SMALL_PREVIEW" ] || { echo "ERROR: $SMALL_PREVIEW missing" >&2; exit 1; }
rm -rf "$OUT"
mkdir -p "$OUT/Localization"
cp "$ROOT/build/$DLL" "$OUT/"
cp "$MANIFEST" "$OUT/"
# 包内放 640x360 的小图：工坊 file_size 只统计 contentfolder
cp "$SMALL_PREVIEW" "$OUT/preview.png"
cp "$ROOT/mod/Localization/"*.csv "$OUT/Localization/"
cp "$ROOT/packaging/README.txt" "$OUT/"

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

LOC_COUNT=$(ls "$OUT/Localization/"*.csv 2>/dev/null | wc -l)
[ "$LOC_COUNT" -ge 2 ] || fail "expected at least 2 localization files, found $LOC_COUNT"
for f in "$OUT/Localization/"*.csv; do
	[ -s "$f" ] || fail "$(basename "$f") is empty"
done

grep -q "<Assembly>$DLL</Assembly>" "$OUT/manifest.xml" || fail "manifest does not list the dll"
grep -q "<Capabilities" "$OUT/manifest.xml" || fail "manifest has no <Capabilities> element"

# 模组扫描器会拒绝的载荷：可执行文件、脚本、未知 DLL、压缩包、美术源文件
BAD=$(find "$OUT" -type f \( -iname '*.exe' -o -iname '*.bat' -o -iname '*.cmd' -o -iname '*.ps1' \
	-o -iname '*.js' -o -iname '*.vbs' -o -iname '*.lnk' -o -iname '*.zip' -o -iname '*.7z' \
	-o -iname '*.rar' -o -iname '*.psd' -o -iname '*.aseprite' -o -iname '*.pdb' -o -iname '*.cs' \
	-o \( -iname '*.dll' ! -iname "$DLL" \) \) -print)
[ -z "$BAD" ] || fail "forbidden files in package: $BAD"

echo "  dll          $(stat -c%s "$OUT/$DLL") bytes"
echo "  preview.png  $PREVIEW_SIZE bytes"
echo "  localization $LOC_COUNT file(s)"
echo "  files        $(find "$OUT" -type f | wc -l)"

echo "== zip =="
ZIP="$DIST/$PKG_NAME.zip"
rm -f "$ZIP"
# cygpath -m 给出 C:/... 形式，VDF 与 Compress-Archive 都不需要转义反斜杠
WIN_OUT="$(cygpath -m "$OUT" 2>/dev/null || echo "$OUT")"
WIN_ZIP="$(cygpath -m "$ZIP" 2>/dev/null || echo "$ZIP")"
powershell -NoProfile -NonInteractive -Command \
	"Compress-Archive -Path '${WIN_OUT}' -DestinationPath '${WIN_ZIP}' -CompressionLevel Optimal -Force" >/dev/null
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
cat > "$VDF" <<EOF
"workshopitem"
{
	"appid"			"4348910"
	"publishedfileid"	"$PUB_ID"
	"contentfolder"		"$WIN_OUT"
	"previewfile"		"$WIN_PREVIEW"
	"visibility"		"$VIS"
	"title"			"删除种类多样 / No More Variety"
	"description"		"删除「种类多样」里的限购：这类客人不再每种只买一件，同一种货可以卖无数次，柜台每件 +15% 价值照旧。Kills the one-per-kind limit: the variety customer now buys as many copies as you can sell, and the +15% counter bonus stays."
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
