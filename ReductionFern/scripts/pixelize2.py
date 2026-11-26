"""Second-stage pixelizer: majority downscale, restricted palette, 1px outline, speck cleanup.

  python scripts/pixelize2.py --src refs/gen/fern_s2.png --grid 16x32 --out refs/pix/fern.png
"""
import argparse
import pathlib
from collections import Counter

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent

# Colors a plant sprite may use (vanilla plant palette subset).
ALLOWED = {
    "#292234", "#275654", "#2f756f", "#45918b", "#8abfbb",
    "#3d823f", "#41603f", "#88948a", "#79746e", "#c5ac96", "#a4715d", "#7d4f4a",
    "#d5d2b8", "#b68b74",
}


def load_allowed(path, allowed):
    colors = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or not line.startswith("#"):
            continue
        h = line.split()[0].lower()
        if h in allowed:
            colors.append(tuple(int(h[1:][i:i + 2], 16) for i in (0, 2, 4)))
    return colors


def key_magenta(img, tolerance=150):
    px = img.convert("RGB").load()
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            # pure magenta and the pale-pink variants the model likes to drift to
            if r > tolerance and b > tolerance and g < min(r, b) - 40:
                continue
            dst[x, y] = (r, g, b, 255)
    return out


def erode_alpha(img):
    """Drop the outer ring of fully opaque pixels so magenta fringe does not survive."""
    px = img.load()
    w, h = img.size
    out = img.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h or px[nx, ny][3] == 0:
                    dst[x, y] = (0, 0, 0, 0)
                    break
    return out


def nearest(color, palette):
    r, g, b = color
    best, bestd = None, 1 << 30
    for pr, pg, pb in palette:
        d = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
        if d < bestd:
            bestd, best = d, (pr, pg, pb)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--palette", default=str(HERE.parent / "refs" / "palette.txt"))
    ap.add_argument("--margin", type=int, default=1)
    ap.add_argument("--scale", type=int, default=16)
    ap.add_argument("--no-outline", action="store_true")
    ap.add_argument("--simple", action="store_true",
                    help="straight BOX resize with no 2x2 majority vote (keeps thin strokes)")
    args = ap.parse_args()

    gw, gh = (int(v) for v in args.grid.lower().split("x"))
    palette = load_allowed(args.palette, ALLOWED)

    sprite = key_magenta(Image.open(args.src))
    sprite = erode_alpha(sprite)
    bbox = sprite.getbbox()
    if not bbox:
        raise SystemExit("nothing left after keying")
    sprite = sprite.crop(bbox)

    inner_w, inner_h = gw - args.margin * 2, gh - args.margin * 2

    if args.simple:
        ratio = min(inner_w / sprite.width, inner_h / sprite.height)
        nw = max(1, round(sprite.width * ratio))
        nh = max(1, round(sprite.height * ratio))
        small = sprite.resize((nw, nh), Image.BOX)
        out = Image.new("RGBA", (gw, gh), (0, 0, 0, 3))
        ox = (gw - nw) // 2
        oy = gh - args.margin - nh
        sp = small.load()
        for y in range(nh):
            for x in range(nw):
                r, g, b, a = sp[x, y]
                if a < 96:
                    continue
                out.putpixel((ox + x, oy + y), nearest((r, g, b), palette) + (255,))
        outpath = pathlib.Path(args.out)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        out.save(outpath)
        big = out.resize((gw * args.scale, gh * args.scale), Image.NEAREST)
        bg = Image.new("RGBA", big.size, (30, 32, 36, 255))
        for y in range(0, big.height, 8):
            for x in range(0, big.width, 8):
                if (x // 8 + y // 8) % 2:
                    for yy in range(y, min(y + 8, big.height)):
                        for xx in range(x, min(x + 8, big.width)):
                            bg.putpixel((xx, yy), (38, 40, 46, 255))
        bg.alpha_composite(big)
        bg.save(outpath.with_name(outpath.stem + "_x%d.png" % args.scale))
        print(f"# wrote {outpath} ({gw}x{gh}) [simple]")
        return

    ratio = min(inner_w / sprite.width, inner_h / sprite.height)
    # render at 2x target, then majority-downsample so block edges stay crisp
    mid_w = max(2, round(sprite.width * ratio * 2))
    mid_h = max(2, round(sprite.height * ratio * 2))
    mid = sprite.resize((mid_w, mid_h), Image.BOX)
    mid = mid.resize((mid_w, mid_h), Image.BOX)

    # quantize to the allowed palette at 2x
    mp = mid.load()
    q = Image.new("RGBA", mid.size, (0, 0, 0, 0))
    qp = q.load()
    for y in range(mid_h):
        for x in range(mid_w):
            r, g, b, a = mp[x, y]
            if a < 128:
                continue
            qp[x, y] = nearest((r, g, b), palette) + (255,)

    # majority 2x2 -> target grid
    out = Image.new("RGBA", (gw, gh), (0, 0, 0, 3))
    ox = (gw - (mid_w + 1) // 2) // 2
    oy = gh - args.margin - (mid_h + 1) // 2
    for y in range((mid_h + 1) // 2):
        for x in range((mid_w + 1) // 2):
            cells = [qp[min(x * 2 + dx, mid_w - 1), min(y * 2 + dy, mid_h - 1)]
                     for dx in (0, 1) for dy in (0, 1)]
            solid = [c for c in cells if c[3] >= 128]
            if len(solid) < 2:
                continue
            color = Counter(solid).most_common(1)[0][0]
            tx, ty = ox + x, oy + y
            if 0 <= tx < gw and 0 <= ty < gh:
                out.putpixel((tx, ty), color)

    if not args.no_outline:
        px = out.load()
        edge = []
        for y in range(gh):
            for x in range(gw):
                if px[x, y][3] < 128:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= gw or ny >= gh or px[nx, ny][3] < 128:
                        edge.append((x, y))
                        break
        for x, y in edge:
            px[x, y] = (0x29, 0x22, 0x34, 255)

    outpath = pathlib.Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    out.save(outpath)
    big = out.resize((gw * args.scale, gh * args.scale), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (30, 32, 36, 255))
    for y in range(0, big.height, 8):
        for x in range(0, big.width, 8):
            if (x // 8 + y // 8) % 2:
                for yy in range(y, min(y + 8, big.height)):
                    for xx in range(x, min(x + 8, big.width)):
                        bg.putpixel((xx, yy), (38, 40, 46, 255))
    bg.alpha_composite(big)
    bg.save(outpath.with_name(outpath.stem + "_x%d.png" % args.scale))
    print(f"# wrote {outpath} ({gw}x{gh})")


if __name__ == "__main__":
    main()
