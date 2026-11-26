"""Final pass for the fiddlehead: keep a 1px margin, then add the 1px dark outline."""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = ROOT / "refs" / "final" / "restoring_fern_s.png"
K = (0x29, 0x22, 0x34, 255)

img = Image.open(src).convert("RGBA")
w, h = img.size
mask = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
bb = mask.getbbox()
dx = max(0, 2 - bb[0])
dy = max(0, 2 - bb[1])
if dx or dy:
    shifted = Image.new("RGBA", (w, h), (0, 0, 0, 3))
    shifted.paste(img, (dx, dy), img)
    img = shifted

px = img.load()
edge = []
for y in range(h):
    for x in range(w):
        if px[x, y][3] > 8:
            continue
        for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + ddx, y + ddy
            if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 8:
                edge.append((x, y))
                break
for x, y in edge:
    px[x, y] = K

img.save(src)
big = img.resize((w * 12, h * 12), Image.NEAREST)
bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
bg.alpha_composite(big)
bg.save(src.with_name(src.stem + "_x12.png"))
print("ok")
