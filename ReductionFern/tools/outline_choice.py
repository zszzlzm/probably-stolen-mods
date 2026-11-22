"""Add a 1px outline around the current sprite and show both versions."""
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
p = ROOT / "refs" / "final" / "restoring_fern_s.png"
img = Image.open(p).convert("RGBA")
px = img.load()
w, h = img.size
K = (0x29, 0x22, 0x34, 255)

edge = []
for y in range(h):
    for x in range(w):
        if px[x, y][3] > 8:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 8:
                edge.append((x, y))
                break

outlined = img.copy()
op = outlined.load()
for x, y in edge:
    op[x, y] = K

scale = 12
sheet = Image.new("RGBA", (2 * (w * scale + 8) + 8, h * scale + 28), (26, 28, 32, 255))
d = ImageDraw.Draw(sheet)
for i, (im, name) in enumerate([(img, "no outline"), (outlined, "outlined")]):
    big = im.resize((w * scale, h * scale), Image.NEAREST)
    sheet.alpha_composite(big, (8 + i * (w * scale + 8), 8))
    d.text((8 + i * (w * scale + 8), h * scale + 12), name, fill=(210, 220, 230))
sheet.save(p.with_name(p.stem + "_outline_choice.png"))
print("edge px:", len(edge))
