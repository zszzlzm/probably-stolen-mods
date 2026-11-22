import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

PY = sys.executable
HERE = pathlib.Path(__file__).resolve().parent
root = HERE.parent

seeds = [10, 11, 12, 13]
cells = []
for s in seeds:
    src = root / "refs" / "gen" / f"fern_s{s}.png"
    out = root / "refs" / "pix" / f"fern_s{s}.png"
    subprocess.run([PY, str(HERE / "pixelize2.py"), "--src", str(src), "--grid", "16x32", "--out", str(out)], check=True)
    cells.append(out)

scale = 10
sheet = Image.new("RGBA", (4 * (16 * scale + 16), 32 * scale + 40), (26, 28, 32, 255))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(cells):
    im = Image.open(p).resize((16 * scale, 32 * scale), Image.NEAREST)
    x = i * (16 * scale + 16) + 8
    sheet.alpha_composite(im, (x, 8))
    d.text((x, 32 * scale + 16), f"s{seeds[i]}", fill=(210, 220, 230, 255))
sheet.save(root / "refs" / "pix" / "fern_candidates.png")
print("ok")
