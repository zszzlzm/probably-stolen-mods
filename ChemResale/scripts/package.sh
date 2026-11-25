#!/usr/bin/env bash
# 打发布包：构建 -> 画封面 -> 组装干净目录 -> 校验 -> 压 zip -> 生成 steamcmd 用 .vdf
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
PKG_NAME="ReagentResale-v$VER"
OUT="$DIST/$PKG_NAME"

echo "== build ($MOD_ID v$VER) =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/ChemResale.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4
[ -s "$ROOT/build/ChemResaleMod.dll" ] || { echo "ERROR: build produced no dll" >&2; exit 1; }

echo "== preview =="
PY="$(bash "$ROOT/scripts/find-python.sh")" || exit 1
# 中文 Windows 上 Python 默认 stdout 是 GBK，写中文描述会炸（U+2212 之类），统一成 UTF-8
export PYTHONIOENCODING=utf-8
"$PY" "$ROOT/scripts/make_cover.py" || { echo "ERROR: cover generation failed" >&2; exit 1; }

echo "== assemble =="
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$ROOT/build/ChemResaleMod.dll" "$OUT/"
cp "$MANIFEST" "$OUT/"
# 工坊的 file_size 只统计 contentfolder，包里放 640x360 的小图；1280 的走 VDF previewfile
cp "$ROOT/build/preview_640.png" "$OUT/preview.png"
cp "$ROOT/packaging/README.txt" "$OUT/"

echo "== verify =="
fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }

[ -s "$OUT/manifest.xml" ] || fail "manifest.xml missing"
[ -s "$OUT/ChemResaleMod.dll" ] || fail "dll missing"
[ -s "$OUT/preview.png" ] || fail "preview.png missing"
PREVIEW_SIZE=$(stat -c%s "$OUT/preview.png")
[ "$PREVIEW_SIZE" -lt 1048576 ] || fail "preview.png is larger than 1 MB ($PREVIEW_SIZE bytes)"

grep -q "<ModVersion>$VER</ModVersion>" "$OUT/manifest.xml" || fail "manifest version mismatch"
grep -q "<Assembly>ChemResaleMod.dll</Assembly>" "$OUT/manifest.xml" || fail "manifest does not list the dll"

"$PY" - "$OUT/preview.png" <<'PYEOF' || fail "preview.png failed the size check"
import sys
from PIL import Image
im = Image.open(sys.argv[1])
print("  preview      %s %s" % (im.size, im.mode))
if im.size != (640, 360):
    sys.exit("expected 640x360, got %s" % (im.size,))
PYEOF

# .NET 把字符串常量存成 UTF-16，grep 找不到，按 UTF-16LE 查
"$PY" - "$OUT/ChemResaleMod.dll" <<'PYEOF' || fail "dll does not reference CHEMICAL_SUPPLIES"
import sys
blob = open(sys.argv[1], "rb").read()
needle = "CHEMICAL_SUPPLIES".encode("utf-16-le")
sys.exit(0 if needle in blob else 1)
PYEOF

BAD=$(find "$OUT" -type f \( -iname '*.exe' -o -iname '*.bat' -o -iname '*.cmd' -o -iname '*.ps1' \
	-o -iname '*.js' -o -iname '*.vbs' -o -iname '*.lnk' -o -iname '*.zip' -o -iname '*.7z' \
	-o -iname '*.rar' -o -iname '*.psd' -o -iname '*.aseprite' -o -iname '*.pdb' \
	-o \( -iname '*.dll' ! -iname 'ChemResaleMod.dll' \) \) -print)
[ -z "$BAD" ] || fail "forbidden files in package: $BAD"

echo "  dll          $(stat -c%s "$OUT/ChemResaleMod.dll") bytes"
echo "  preview.png  $PREVIEW_SIZE bytes"
echo "  files        $(find "$OUT" -type f | wc -l)"

echo "== zip =="
ZIP="$DIST/$PKG_NAME.zip"
rm -f "$ZIP"
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
VDF="$DIST/$MOD_ID.vdf"
WIN_PREVIEW="$(cygpath -m "$ROOT/mod/preview.png" 2>/dev/null || echo "$ROOT/mod/preview.png")"
PUB_ID="0"
VIS="2"
if [ -f "$VDF" ]; then
	PREV_ID="$(grep -oE '"publishedfileid"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_ID:-}" ] && PUB_ID="$PREV_ID"
	PREV_VIS="$(grep -oE '"visibility"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_VIS:-}" ] && VIS="$PREV_VIS"
fi
VIS="${VIS_OVERRIDE:-$VIS}"
CHANGENOTE="${CHANGENOTE:-v$VER。}"

# 工坊长描述直接写进 vdf，省掉每次上线手动粘贴。
# 坑：Steam 的 KeyValues **没有转义**，值里出现 ASCII 双引号会提前截断字符串、
# 整个 vdf 解析失败（"Bad expression token"）。所以源文件里禁止 ASCII 引号，用中文引号。
# 反斜杠是字面量，不用转义；换行在值里合法。
DESC_FILE="$ROOT/packaging/workshop_description.txt"
[ -s "$DESC_FILE" ] || { echo "ERROR: $DESC_FILE missing" >&2; exit 1; }
DESC_ESC="$("$PY" -c '
import sys
t = open(sys.argv[1], encoding="utf-8").read().rstrip()
bad = [i + 1 for i, l in enumerate(t.split("\n")) if chr(34) in l]
if bad:
    sys.stderr.write("ERROR: ASCII double quote in %s at line(s) %s; "
                     "KeyValues cannot escape it, use \u201c \u201d instead\n"
                     % (sys.argv[1], ", ".join(map(str, bad))))
    raise SystemExit(1)
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
	"title"			"试剂可售 / Reagent Resale"
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
