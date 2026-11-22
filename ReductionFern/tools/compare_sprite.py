"""Side-by-side comparison of a generated sprite against vanilla references at 16x."""
import pathlib
import sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
VANILLA = ROOT / "refs" / "vanilla"


def label(im, text, scale):
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    pad = 8
    canvas = Image.new("RGBA", (big.width + pad * 2, big.height + 28), (26, 28, 32, 255))
    canvas.alpha_composite(big, (pad, pad))
    d = ImageDraw.Draw(canvas)
    d.text((pad, big.height + pad + 2), text, fill=(210, 220, 230, 255))
    return canvas


def main():
    src = pathlib.Path(sys.argv[1])
    refs = sys.argv[2:] or ["dream_cap_seed", "hydroreed_seed"]
    scale = 12
    items = [label(Image.open(src).convert("RGBA"), src.stem, scale)]
    for r in refs:
        p = VANILLA / f"{r}__resources.png"
        items.append(label(Image.open(p).convert("RGBA"), r, scale))

    w = sum(i.width for i in items) + 12 * (len(items) + 1)
    h = max(i.height for i in items) + 24
    sheet = Image.new("RGBA", (w, h), (26, 28, 32, 255))
    x = 12
    for i in items:
        sheet.alpha_composite(i, (x, 12))
        x += i.width + 12
    out = src.with_name(src.stem + "_compare.png")
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
