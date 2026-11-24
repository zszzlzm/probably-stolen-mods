#!/usr/bin/env bash
# 打发布包：构建 -> 组装干净的模组文件夹 -> 校验 -> 压 zip -> 生成 steamcmd 上传用 .vdf
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
PKG_NAME="Pharmacy-v$VER"
OUT="$DIST/$PKG_NAME"

echo "== build ($MOD_ID v$VER) =="
DOTNET_CLI_UI_LANGUAGE=en dotnet build "$ROOT/Pharmacy.csproj" -c Release -o "$ROOT/build" -v:minimal | tail -4
[ -s "$ROOT/build/PharmacyMod.dll" ] || { echo "ERROR: build produced no dll" >&2; exit 1; }

echo "== assemble =="
rm -rf "$OUT"
mkdir -p "$OUT/Localization"
cp "$ROOT/build/PharmacyMod.dll" "$OUT/"
cp "$MANIFEST" "$OUT/"
cp -r "$ROOT/mod/Textures" "$OUT/Textures"
cp "$ROOT/mod/preview.png" "$OUT/"
cp "$ROOT/mod/Localization/"*.csv "$OUT/Localization/"
cp "$ROOT/packaging/README.txt" "$OUT/"

echo "== verify =="
fail() { echo "VERIFY FAILED: $*" >&2; exit 1; }

[ -s "$OUT/manifest.xml" ] || fail "manifest.xml missing"
[ -s "$OUT/PharmacyMod.dll" ] || fail "dll missing"
[ -s "$OUT/preview.png" ] || fail "preview.png missing"
PREVIEW_SIZE=$(stat -c%s "$OUT/preview.png")
[ "$PREVIEW_SIZE" -lt 1048576 ] || fail "preview.png is larger than 1 MB ($PREVIEW_SIZE bytes)"

LOC_COUNT=$(ls "$OUT/Localization/"*.csv 2>/dev/null | wc -l)
[ "$LOC_COUNT" -ge 2 ] || fail "expected at least 2 localization files, found $LOC_COUNT"
for f in "$OUT/Localization/"*.csv; do
	[ -s "$f" ] || fail "$(basename "$f") is empty"
done

SPRITES=$(find "$OUT/Textures" -name '*.png' | wc -l)
[ "$SPRITES" -ge 2 ] || fail "expected 2 item sprites, found $SPRITES"

grep -q "<Assembly>PharmacyMod.dll</Assembly>" "$OUT/manifest.xml" || fail "manifest does not list the dll"
grep -q "<Capabilities" "$OUT/manifest.xml" || fail "manifest has no <Capabilities> element"

BAD=$(find "$OUT" -type f \( -iname '*.exe' -o -iname '*.bat' -o -iname '*.cmd' -o -iname '*.ps1' \
	-o -iname '*.js' -o -iname '*.vbs' -o -iname '*.lnk' -o -iname '*.zip' -o -iname '*.7z' \
	-o -iname '*.rar' -o -iname '*.psd' -o -iname '*.aseprite' -o -iname '*.pdb' \
	-o \( -iname '*.dll' ! -iname 'PharmacyMod.dll' \) \) -print)
[ -z "$BAD" ] || fail "forbidden files in package: $BAD"

echo "  dll          $(stat -c%s "$OUT/PharmacyMod.dll") bytes"
echo "  preview.png  $PREVIEW_SIZE bytes"
echo "  localization $LOC_COUNT file(s)"
echo "  sprites      $SPRITES"
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
VDF="$DIST/${MOD_ID}.vdf"
# 工坊封面用 mod/preview.png（1280 全画质，不计入包体积）；包内那张是 640x360 缩略图。
WIN_PREVIEW="$(cygpath -m "$ROOT/mod/preview.png" 2>/dev/null || echo "$ROOT/mod/preview.png")"
# 已经上传过的模组：沿用原 publishedfileid 和 visibility，否则 steamcmd 会新建重复条目
# 或把已经公开的物品改回隐藏。
PUB_ID="0"
VIS="2"
if [ -f "$VDF" ]; then
	PREV_ID="$(grep -oE '"publishedfileid"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_ID:-}" ] && PUB_ID="$PREV_ID"
	PREV_VIS="$(grep -oE '"visibility"[[:space:]]*"[0-9]+"' "$VDF" | grep -oE '[0-9]+' | head -1 || true)"
	[ -n "${PREV_VIS:-}" ] && VIS="$PREV_VIS"
fi
# 仍然允许命令行临时指定：VIS=0 ./package.sh
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
	"title"			"下层药房 / Lower-District Pharmacy"
	"description"		"两种可以在化学精制机上自制的合法药品：澄心剂（0.8ml 梦帽菇萃取液，价值 12）与消痛片（0.08ml 芬太，价值 20）。带医疗品/麻醉品/烟酒类标签，没有违禁品标签。Two legal medicines for the chem finisher: Calming Agent (0.8 ml dream-cap extract, value 12) and Pain Relief Tablet (0.08 ml fentanyl, value 20)."
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
