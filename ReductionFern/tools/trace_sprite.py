"""Trace a model render into a flat, grid-snapped sprite (no mush, no lost gaps).

  python tools/trace_sprite.py --src refs/gen/fern_s203.png --grid 16x32 \
      --out refs/final/restoring_fern.png

The Qwen render uses ~32 px per logical pixel but is not aligned to that grid, so a
naive downscale smears leaflets together. Here each target cell takes a coverage
vote for the silhouette and a colour vote from the model pixels inside it: that keeps
the 3-frond structure and the 1-px gaps between leaflets, while every pixel ends up
one of the flat palette colours.
"""
import argparse
import pathlib
from collections import deque

from PIL import Image

PAL = {
    "G": (0x3D, 0x82, 0x3F),
    "g": (0x41, 0x60, 0x3F),
    "T": (0x2F, 0x75, 0x6F),
    "B": (0x45, 0x91, 0x8B),
    "L": (0x8A, 0xBF, 0xBB),
    "D": (0x27, 0x56, 0x54),
    "K": (0x29, 0x22, 0x34),
}
BG = (0, 0, 0, 3)


def key_magenta(img, tol=150):
    px = img.convert("RGB").load()
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > tol and b > tol and g < min(r, b) - 40:
                continue
            dst[x, y] = (r, g, b, 255)
    return out


def outline(g):
    h, w = len(g), len(g[0])
    outside = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if g[y][x] == ".":
                outside[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if g[y][x] == "." and not outside[y][x]:
                outside[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not outside[ny][nx] and g[ny][nx] == ".":
                outside[ny][nx] = True
                q.append((nx, ny))
    out = [row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] != "." or not outside[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and g[ny][nx] != ".":
                    out[y][x] = "K"
                    break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--cover", type=float, default=0.40)
    args = ap.parse_args()
    gw, gh = (int(v) for v in args.grid.lower().split("x"))

    sprite = key_magenta(Image.open(args.src))
    bbox = sprite.getbbox()
    if not bbox:
        raise SystemExit("nothing after keying")
    sprite = sprite.crop(bbox)

    iw, ih = gw - 2 * args.margin, gh - 2 * args.margin
    # fit inside the inner box, keeping the model's aspect
    ratio = min(iw / sprite.width, ih / sprite.height)
    nw = max(1, round(sprite.width * ratio))
    nh = max(1, round(sprite.height * ratio))

    small = sprite.resize((nw, nh), Image.BOX)
    mask = sprite.getchannel("A").resize((nw, nh), Image.BOX)

    g = [["." for _ in range(gw)] for _ in range(gh)]
    ox = (gw - nw) // 2
    oy = gh - args.margin - nh

    sp, mp = small.load(), mask.load()
    for y in range(nh):
        for x in range(nw):
            cover = mp[x, y] / 255.0
            if cover < args.cover:
                continue
            r, gg, b, _ = sp[x, y]
            # teal stem: blue >= green and clearly not the leaf green
            if b > r + 20 and b >= gg - 10:
                c = "T" if cover > 0.55 else "D"
                if gg > 150 and b > 150:
                    c = "B"
            else:
                c = "G"
            g[oy + y][ox + x] = c

    g = outline(g)

    img = Image.new("RGBA", (gw, gh), BG)
    for y in range(gh):
        for x in range(gw):
            if g[y][x] != ".":
                img.putpixel((x, y), PAL[g[y][x]] + (255,))
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    big = img.resize((gw * 12, gh * 12), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
    bg.alpha_composite(big)
    bg.save(out.with_name(out.stem + "_x12.png"))
    counts = {}
    for row in g:
        for c in row:
            if c != ".":
                counts[c] = counts.get(c, 0) + 1
    print("# colors:", sorted(counts.items()))
    for row in g:
        print("".join(row))


if __name__ == "__main__":
    main()
