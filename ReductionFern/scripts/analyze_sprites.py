"""Analyze vanilla sprites: alpha bbox, palette, edge margins."""
import json
import os
import sys
from collections import Counter

from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else "refs/vanilla"
with open(os.path.join(src, "sprites.json"), encoding="utf-8") as fh:
    meta = json.load(fh)

for m in meta:
    img = Image.open(os.path.join(src, m["png"])).convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    colors = [c for c in img.getdata() if c[3] > 0]
    cnt = Counter(colors)
    opaque = sum(cnt.values())
    print(f"== {m['name']} {img.size} bbox={bbox} colors={len(cnt)} opaque_px={opaque}")
    for color, n in cnt.most_common(12):
        print(f"   #{color[0]:02x}{color[1]:02x}{color[2]:02x} a={color[3]:3d}  {n}")
