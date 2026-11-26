"""Build the sprite sheet: all five fern sprites at 6x with a 1x thumbnail.

    python scripts/tier_sheet.py

The three leaf tiers share one item id, so they are shown together to check that the
weight of the drawing grows with the slot size; the seed and the hydroponic portrait
are included because they sit next to them in the mod's UI.
"""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
FINAL = ROOT / "refs" / "final"
SCALE = 6

SPRITES = [
    ("restoring_fern_seed", "seed 16x16"),
    ("restoring_fern_s", "small 16x16"),
    ("restoring_fern", "standard 16x32"),
    ("restoring_fern_l", "large 32x32"),
    ("restoring_fern_p", "hydro 48x64"),
]


def main():
    sizes = [Image.open(FINAL / f"{name}.png").size for name, _ in SPRITES]
    cell_w = max(w for w, _ in sizes) * SCALE
    cell_h = max(h for _, h in sizes) * SCALE
    pad = 16
    width = sum(cell_w + pad for _ in SPRITES) + pad
    height = cell_h + 52

    sheet = Image.new("RGBA", (width, height), (26, 28, 32, 255))
    draw = ImageDraw.Draw(sheet)

    x = pad
    for name, label in SPRITES:
        sprite = Image.open(FINAL / f"{name}.png").convert("RGBA")
        big = sprite.resize((sprite.width * SCALE, sprite.height * SCALE), Image.NEAREST)
        sheet.alpha_composite(big, (x + (cell_w - big.width) // 2, pad + (cell_h - big.height)))
        draw.text((x, cell_h + pad + 10), label, fill=(210, 220, 230, 255))
        x += cell_w + pad

    out = FINAL / "sprite_sheet.png"
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
