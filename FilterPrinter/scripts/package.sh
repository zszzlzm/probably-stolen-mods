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
PY="${DSH_PYTHON:-/c/Users/zszzl/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe}"
if [ ! -x "$PY" ]; then
	PY="$(command -v python3 || command -v python || true)"
fi
[ -n "$PY" ] || { echo "ERROR: no python interpreter found" >&2; exit 1; }
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
cp "$ROOT/packaging/README.txt" "$OUT/"

echo "== verify =="
fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }

[ -s "$OUT/manifest.xml" ] || fail "manifest.xml missing"
[ -s "$OUT/FilterPrinterMod.dll" ] || fail "dll missing"
[ -s "$OUT/preview.png" ] || fail "preview.png missing"
PREVIEW_SIZE=$(stat -c%s "$OUT/preview.png")
[ "$PREVIEW_SIZE" -lt 1048576 ] || fail "preview.png is larger than 1 MB ($PREVIEW_SIZE bytes)"

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
cat > "$VDF" <<EOF
"workshopitem"
{
	"appid"			"4348910"
	"publishedfileid"	"$PUB_ID"
	"contentfolder"		"$WIN_OUT"
	"previewfile"		"$WIN_PREVIEW"
	"visibility"		"$VIS"
	"title"			"滤芯打印机 / Filter Cartridge Printer"
	"description"		"按你指定的截留物质打印专用滤芯：重金属、微塑料、微生物、药物、化学品、营养物……共 37 种，打印一次 120 电。Print a filter cartridge for exactly the substance you choose - 37 types, 120 power each."
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
