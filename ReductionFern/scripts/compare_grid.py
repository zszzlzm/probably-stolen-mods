import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

PY = sys.executable
HERE = pathlib.Path(__file__).resolve().parent
root = HERE.parent

seeds = [2, 10, 11, 12, 13]
grid = sys.argv[1] if len(sys.argv) > 1 else "32x32"
gw, gh = (int(v) for v in grid.split("x"))
scale = max(4, 400 // gh)
cells = []
for s in seeds:
    src = root / "refs" / "gen" / f"fern_s{s}.png"
    out = root / "refs" / "pix" / f"fern_{grid}_s{s}.png"
    subprocess.run([PY, str(HERE / "pixelize2.py"), "--src", str(src), "--grid", grid, "--out", str(out),
                    "--scale", str(scale)], check=True)
    cells.append(out)

sheet = Image.new("RGBA", (len(cells) * (gw * scale + 16), gh * scale + 40), (26, 28, 32, 255))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(cells):
    im = Image.open(p).resize((gw * scale, gh * scale), Image.NEAREST)
    x = i * (gw * scale + 16) + 8
    sheet.alpha_composite(im, (x, 8))
    d.text((x, gh * scale + 16), f"s{seeds[i]}", fill=(210, 220, 230, 255))
out = root / "refs" / "pix" / f"fern_candidates_{grid}.png"
sheet.save(out)
print(out)
