"""Compose a labeled contact sheet of sprites for visual inspection (nearest-neighbour upscale)."""
import json
import os
import sys

from PIL import Image, ImageDraw

src = sys.argv[1] if len(sys.argv) > 1 else "refs/vanilla"
out = sys.argv[2] if len(sys.argv) > 2 else "refs/vanilla_sheet.png"
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 8

with open(os.path.join(src, "sprites.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

cell_w = max(m["size"][0] for m in meta) * scale + 24
cell_h = max(m["size"][1] for m in meta) * scale + 40
cols = 5
rows = (len(meta) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * cell_w, rows * cell_h), (28, 30, 34, 255))
draw = ImageDraw.Draw(sheet)

for i, m in enumerate(meta):
    img = Image.open(os.path.join(src, m["png"])).convert("RGBA")
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    x = (i % cols) * cell_w + 12
    y = (i // cols) * cell_h + 12
    sheet.alpha_composite(big, (x, y))
    label = f"{m['name']} {m['size'][0]}x{m['size'][1]}"
    draw.text((x, y + big.height + 4), label, fill=(200, 210, 220, 255))

sheet.save(out)
print(f"# {out} {sheet.size}")
