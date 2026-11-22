"""Place a pixelized portrait sprite into the vanilla ``_p`` box and flatten its palette.

    python tools/place_portrait.py refs/pix/plant_p_301.png refs/final/restoring_fern_p.png

The vanilla growth sprites keep their artwork inside rows 11-46 and columns 1-46. The
model render has a different aspect and sits lower, so the content is shifted into that
box, snapped to the mod palette (which also caps the colour count), and given the 1 px
plum outline.
"""
import argparse
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from frond_art import COLORS  # noqa: E402
from pixel_art import TRANSPARENT  # noqa: E402

CONTENT_BOTTOM = 45   # outline then occupies row 46, like the vanilla sprites
CONTENT_TOP_MIN = 11


def nearest(rgb, palette):
    r, g, b = rgb
    return min(
        palette,
        key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    bbox = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bbox:
        raise SystemExit("empty sprite")
    left, top, right, bottom = bbox

    # centre horizontally, sit the roots just above the bottom margin
    dx = (w - (right - left)) // 2 - left
    dy = CONTENT_BOTTOM - (bottom - 1)
    shifted = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shifted.paste(img, (dx, dy), img)

    # flatten to the mod palette (7 colours, so the sprite passes the colour cap)
    palette = list(COLORS.values())
    px = shifted.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 3))
    dst_px = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 96:
                continue
            dst_px[x, y] = nearest((r, g, b), palette) + (255,)

    # The model paints the frond tips almost white. At 48x64 that becomes a handful of
    # pale blue squares that read as flowers, so the pale tone is folded into the mid
    # teal - the clump keeps its green/teal ramp and loses the speckle.
    pale = COLORS["L"]
    mid = COLORS["B"]
    for y in range(h):
        for x in range(w):
            if dst_px[x, y][:3] == pale:
                dst_px[x, y] = mid + (255,)

    # trim one pixel protrusions (bare stem tips) so the silhouette has no antennae
    for _ in range(2):
        thin = []
        for y in range(h):
            for x in range(w):
                if dst_px[x, y][3] <= 8:
                    continue
                neighbours = 0
                for ny in (y - 1, y, y + 1):
                    for nx in (x - 1, x, x + 1):
                        if (nx, ny) != (x, y) and 0 <= nx < w and 0 <= ny < h and dst_px[nx, ny][3] > 8:
                            neighbours += 1
                if neighbours <= 1:
                    thin.append((x, y))
        if not thin:
            break
        for x, y in thin:
            dst_px[x, y] = (0, 0, 0, 3)

    # 1 px plum outline on the exterior (collect, then paint)
    k = COLORS["K"]
    edge = []
    for y in range(h):
        for x in range(w):
            if dst_px[x, y][3] > 8:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and dst_px[nx, ny][3] > 8:
                    edge.append((x, y))
                    break
    for x, y in edge:
        dst_px[x, y] = k + (255,)

    dst = pathlib.Path(args.dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    for scale, suffix in ((1, "_x1"), (12, "_x12")):
        big = out.resize((w * scale, h * scale), Image.NEAREST)
        bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
        bg.alpha_composite(big)
        bg.save(dst.with_name(dst.stem + suffix + ".png"))

    tally = {}
    for y in range(h):
        for x in range(w):
            c = dst_px[x, y]
            if c[3] > 8:
                tally["#%02x%02x%02x" % c[:3]] = tally.get("#%02x%02x%02x" % c[:3], 0) + 1
    print("bbox", out.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())
    print("colors", sorted(tally.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    main()
