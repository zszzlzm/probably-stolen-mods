#!/usr/bin/env bash
# 打发布包：构建 -> 组装干净的模组文件夹 -> 校验 -> 压 zip -> 生成 steamcmd 上传用 .vdf
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/mod/manifest.xml"
DIST="$ROOT/dist"

VER="$(grep -o '<ModVersion>[^<]*' "$MANIFEST" | head -1 | sed 's/<ModVersion>//')"
MOD_ID="$(grep -o '<ID>[^<]*' "$MANIFEST" | head -1 | sed 's/<ID>//')"
NAME_ZH="$(grep -o '<Name>[^<]*' "$MANIFEST" | head -1 | sed 's/<Name>//')"
if [ -z "$VER" ] || [ -z "$MOD_ID" ]; then
	echo "ERROR: cannot read ModVersion/ID from $MANIFEST" >&2
	exit 1
fi
PKG_NAME="FilterPrinter-v$VER"
OUT="$DIST/$PKG_NAME"

echo "== build ($MOD_ID v$VER) =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/FilterPrinter.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4
[ -s "$ROOT/build/FilterPrinterMod.dll" ] || { echo "ERROR: build produced no dll" >&2; exit 1; }

echo "== preview =="
# 需要 Python 3 + Pillow。不要用 `command -v python3`：这台机器上是应用商店的占位程序（退出 49）。
# 中文 Windows 上 Python 的 stdout 默认 GBK，写中文进 vdf 会 UnicodeEncodeError，统一 UTF-8。
PY="$(bash "$ROOT/../tools/find-python.sh" "import PIL")" || exit 1
export PYTHONIOENCODING=utf-8
KEYART="$ROOT/refs/gen/keyart.png"
if [ -f "$KEYART" ]; then
	"$PY" "$ROOT/scripts/make_cover.py" "$KEYART" || { echo "ERROR: preview generation failed" >&2; exit 1; }
else
	"$PY" "$ROOT/scripts/make_preview.py" || { echo "ERROR: preview generation failed" >&2; exit 1; }
fi

echo "== assemble =="
rm -rf "$OUT"
mkdir -p "$OUT/Localization"
cp "$ROOT/build/FilterPrinterMod.dll" "$OUT/"
cp "$MANIFEST" "$OUT/"
cp "$ROOT/mod/preview.png" "$OUT/"
cp "$ROOT/mod/Localization/"*.csv "$OUT/Localization/"
if [ -d "$ROOT/mod/Textures/Items" ]; then
	mkdir -p "$OUT/Textures/Items"
	cp "$ROOT/mod/Textures/Items/"*.png "$OUT/Textures/Items/"
fi
cp "$ROOT/packaging/README.txt" "$OUT/"

echo "== verify =="
fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }

[ -s "$OUT/manifest.xml" ] || fail "manifest.xml missing"
[ -s "$OUT/FilterPrinterMod.dll" ] || fail "dll missing"
[ -s "$OUT/preview.png" ] || fail "preview.png missing"
PREVIEW_SIZE=$(stat -c%s "$OUT/preview.png")
[ "$PREVIEW_SIZE" -lt 1048576 ] || fail "preview.png is larger than 1 MB ($PREVIEW_SIZE bytes)"

# 专用贴图：必须是 48x48（16px 网格 3x3），否则物品占位和原版打印机不一致
SPRITE="$OUT/Textures/Items/fp_printer.png"
[ -s "$SPRITE" ] || fail "Textures/Items/fp_printer.png missing"
"$PY" - "$SPRITE" <<'PYEOF' || fail "fp_printer.png failed the size/mode check"
import sys
from PIL import Image
im = Image.open(sys.argv[1])
print("  sprite       %s %s" % (im.size, im.mode))
if im.size != (48, 48):
    sys.exit("expected 48x48, got %s" % (im.size,))
if im.mode != "RGBA":
    sys.exit("expected RGBA, got %s" % (im.mode,))
PYEOF
# .NET 把字符串常量存成 UTF-16，grep 找不到 "fp_printer"，用 python 按 UTF-16LE 查
"$PY" - "$OUT/FilterPrinterMod.dll" <<'PYEOF' || fail "dll does not reference the fp_printer sprite key"
import sys
blob = open(sys.argv[1], "rb").read()
needle = "fp_printer".encode("utf-16-le")
sys.exit(0 if needle in blob else 1)
PYEOF

LOC_COUNT=$(ls "$OUT/Localization/"*.csv 2>/dev/null | wc -l)
[ "$LOC_COUNT" -ge 2 ] || fail "expected at least 2 localization files, found $LOC_COUNT"
for f in "$OUT/Localization/"*.csv; do
	[ -s "$f" ] || fail "$(basename "$f") is empty"
done

grep -q "<Assembly>FilterPrinterMod.dll</Assembly>" "$OUT/manifest.xml" || fail "manifest does not list the dll"
grep -q "<Capabilities" "$OUT/manifest.xml" || fail "manifest has no <Capabilities> element"

# 模组扫描器会拒绝的载荷：可执行文件、脚本、未知 DLL、压缩包、美术源文件
BAD=$(find "$OUT" -type f \( -iname '*.exe' -o -iname '*.bat' -o -iname '*.cmd' -o -iname '*.ps1' \
	-o -iname '*.js' -o -iname '*.vbs' -o -iname '*.lnk' -o -iname '*.zip' -o -iname '*.7z' \
	-o -iname '*.rar' -o -iname '*.psd' -o -iname '*.aseprite' -o -iname '*.pdb' \
	-o \( -iname '*.dll' ! -iname 'FilterPrinterMod.dll' \) \) -print)
[ -z "$BAD" ] || fail "forbidden files in package: $BAD"

echo "  dll          $(stat -c%s "$OUT/FilterPrinterMod.dll") bytes"
echo "  preview.png  $PREVIEW_SIZE bytes"
echo "  localization $LOC_COUNT file(s)"
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
WIN_PREVIEW="$(cygpath -m "$OUT/preview.png" 2>/dev/null || echo "$OUT/preview.png")"
# 已经上传过的模组：沿用原 publishedfileid 和 visibility，否则会新建重复条目或把公开条目改回隐藏。
PUB_ID="0"
VIS="2"
if [ -f "$VDF" ]; then
	PREV_ID="$(grep -oE '"publishedfileid"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_ID:-}" ] && PUB_ID="$PREV_ID"
	PREV_VIS="$(grep -oE '"visibility"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_VIS:-}" ] && VIS="$PREV_VIS"
fi
VIS="${VIS_OVERRIDE:-$VIS}"
CHANGENOTE="${CHANGENOTE:-v$VER 更新。}"

# 工坊长描述直接写进 vdf，省掉每次上线手动粘贴。
# 坑：KeyValues **没有转义**，值里的 ASCII 双引号会提前截断字符串、整份 vdf 解析失败。
# 所以源文件禁止 ASCII 引号（用中文引号），反斜杠是字面量、换行在值里合法。
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
	"title"			"滤芯打印机 / Filter Cartridge Printer"
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
