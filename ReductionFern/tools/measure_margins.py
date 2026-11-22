"""Measure vanilla content margins (ignoring the alpha=3 filler) for the art spec."""
import json
import os

from PIL import Image

SRC = "refs/vanilla"
with open(os.path.join(SRC, "sprites.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

names = ["dream_cap", "dream_cap_s", "dream_cap_l", "dream_cap_seed",
         "hydroreed_filter", "hydroreed_seed", "hydroreed_p",
         "fillerweed", "kotton_plant", "nutrifruit"]
for m in meta:
    if m["name"] not in names:
        continue
    img = Image.open(os.path.join(SRC, m["png"])).convert("RGBA")
    w, h = img.size
    mask = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    bbox = mask.getbbox()
    if not bbox:
        continue
    left, top, right, bottom = bbox
    print(f"{m['name']:18s} {w:2d}x{h:2d}  content={right-left:2d}x{bottom-top:2d}"
          f"  margins L{left} T{top} R{w-right} B{h-bottom}")
