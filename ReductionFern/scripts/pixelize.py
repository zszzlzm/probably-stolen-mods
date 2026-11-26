"""Key the magenta background, snap the sprite to a 16px-grid size and quantize it to the vanilla palette.

  python scripts/pixelize.py --src refs/gen/fern_s2.png --grid 16x32 --out refs/pix/fern.png
"""
import argparse
import pathlib

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent


def load_palette(path):
    colors = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or not line.startswith("#"):
            continue
        hexpart = line.split()[0][1:]
        colors.append(tuple(int(hexpart[i:i + 2], 16) for i in (0, 2, 4)))
    return colors


def key_magenta(img):
    px = img.convert("RGB").load()
    w, h = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 170 and b > 170 and g < 110 and abs(r - b) < 90:
                continue
            dst[x, y] = (r, g, b, 255)
    return out


def nearest(color, palette):
    r, g, b = color
    best = None
    bestd = 1 << 30
    for pr, pg, pb in palette:
        d = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
        if d < bestd:
            bestd = d
            best = (pr, pg, pb)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--grid", required=True, help="WxH, e.g. 16x32")
    ap.add_argument("--out", required=True)
    ap.add_argument("--palette", default=str(HERE.parent / "refs" / "palette.txt"))
    ap.add_argument("--margin", type=int, default=1, help="transparent margin in target pixels")
    ap.add_argument("--scale", type=int, default=16, help="preview upscale")
    args = ap.parse_args()

    gw, gh = (int(v) for v in args.grid.lower().split("x"))
    palette = load_palette(args.palette)

    sprite = key_magenta(Image.open(args.src))
    bbox = sprite.getbbox()
    if not bbox:
        raise SystemExit("no sprite found after keying")
    sprite = sprite.crop(bbox)

    inner_w = gw - args.margin * 2
    inner_h = gh - args.margin * 2
    ratio = min(inner_w / sprite.width, inner_h / sprite.height)
    new_w = max(1, round(sprite.width * ratio))
    new_h = max(1, round(sprite.height * ratio))
    small = sprite.resize((new_w, new_h), Image.BOX)

    out = Image.new("RGBA", (gw, gh), (0, 0, 0, 3))
    ox = (gw - new_w) // 2
    oy = gh - args.margin - new_h  # sit on the bottom, like a standing item
    px = small.load()
    dst = out.load()
    for y in range(new_h):
        for x in range(new_w):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            dst[ox + x, oy + y] = nearest((r, g, b), palette) + (255,)

    outpath = pathlib.Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    out.save(outpath)

    big = out.resize((gw * args.scale, gh * args.scale), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (30, 32, 36, 255))
    for y in range(0, big.height, 8):  # light checker to reveal transparency
        for x in range(0, big.width, 8):
            if (x // 8 + y // 8) % 2:
                for yy in range(y, min(y + 8, big.height)):
                    for xx in range(x, min(x + 8, big.width)):
                        bg.putpixel((xx, yy), (38, 40, 46, 255))
    bg.alpha_composite(big)
    preview = outpath.with_name(outpath.stem + "_x%d.png" % args.scale)
    bg.save(preview)
    print(f"# wrote {outpath} ({gw}x{gh}) and {preview}")


if __name__ == "__main__":
    main()
