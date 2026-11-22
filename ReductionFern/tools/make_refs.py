"""Build a shared palette from vanilla plant sprites and make padded, upscaled refs for the model."""
import json
import os

from PIL import Image

SRC = "refs/vanilla"
OUT = "refs/model"
SCALE = 16

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(SRC, "sprites.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

colors = {}
for m in meta:
    img = Image.open(os.path.join(SRC, m["png"])).convert("RGBA")
    for c in set(img.getdata()):
        if c[3] > 8:
            colors[c[:3]] = colors.get(c[:3], 0) + 1

palette = sorted(colors, key=lambda c: (-colors[c], c))
with open("refs/palette.txt", "w", encoding="utf-8") as fh:
    for c in palette:
        fh.write("#%02x%02x%02x %d\n" % (c[0], c[1], c[2], colors[c]))
print(f"# palette colors: {len(palette)}")
for c in palette:
    print("#%02x%02x%02x %3d" % (c[0], c[1], c[2], colors[c]))

# refs: nearest-neighbour upscale on a flat magenta background, with a thin border
for m in meta:
    img = Image.open(os.path.join(SRC, m["png"])).convert("RGBA")
    big = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
    pad = 32
    canvas = Image.new("RGB", (big.width + pad * 2, big.height + pad * 2), (255, 0, 255))
    canvas.paste(big, (pad, pad), big)
    canvas.save(os.path.join(OUT, m["name"] + "_ref.png"))
print("# refs written to", OUT)
