"""Targeted touch-up for the fiddlehead: unify tones, thicken the stem, keep a 1px margin."""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = ROOT / "refs" / "pix" / "fern_s_base.png"
out = ROOT / "refs" / "final" / "restoring_fern_s.png"

L = (0x8A, 0xBF, 0xBB, 255)
K = (0x29, 0x22, 0x34, 255)

img = Image.open(src).convert("RGBA")
px = img.load()
w, h = img.size

# unify the washed-out creams/greys into the pale teal so the curl reads as one plant
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if (r, g, b) in ((0xD5, 0xD2, 0xB8), (0x88, 0x94, 0x8A), (0x79, 0x74, 0x6E)):
            px[x, y] = L

# thicken the stem below the curl: copy column 3 into column 4 when empty
for y in range(9, 15):
    if px[3, y][3] > 8 and px[4, y][3] <= 8:
        px[4, y] = px[3, y]

# pad so the outline (added next) leaves a 1px margin
mask = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
bbox = mask.getbbox()
dx = max(0, 2 - bbox[0])
dy = max(0, 2 - bbox[1])
if dx or dy:
    shifted = Image.new("RGBA", (w, h), (0, 0, 0, 3))
    shifted.paste(img, (dx, dy), img)
    img = shifted
    px = img.load()

# outline the silhouette
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

out.parent.mkdir(parents=True, exist_ok=True)
img.save(out)
big = img.resize((w * 12, h * 12), Image.NEAREST)
bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
bg.alpha_composite(big)
bg.save(out.with_name(out.stem + "_x12.png"))
print("ok", out)
