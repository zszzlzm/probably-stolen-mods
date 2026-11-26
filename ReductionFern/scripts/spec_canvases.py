"""Draw the planned canvases with their 16px grid and 1px safe margin (vertical spec sheet)."""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANVASES = [
    ("restoring_fern_seed", 16, 16, "1x1  spore vial"),
    ("restoring_fern_s", 16, 16, "1x1  curled frond"),
    ("restoring_fern", 16, 32, "1x2  standard frond"),
    ("restoring_fern_l", 32, 32, "2x2  large frond"),
    ("restoring_fern_p", 48, 64, "48x64  hydroponic stage"),
]
SCALE = 8
PAD = 18
LABEL_W = 340

rows = []
for name, w, h, desc in CANVASES:
    im = Image.new("RGBA", (w * SCALE, h * SCALE), (22, 24, 28, 255))
    d = ImageDraw.Draw(im)
    for x in range(0, w * SCALE + 1, 16 * SCALE):
        d.line([(x, 0), (x, h * SCALE)], fill=(70, 76, 86, 255))
    for y in range(0, h * SCALE + 1, 16 * SCALE):
        d.line([(0, y), (w * SCALE, y)], fill=(70, 76, 86, 255))
    dash = (230, 120, 120, 255)
    s = SCALE
    for t in range(0, w * SCALE - 2 * s, 8):
        d.line([(s + t, s), (s + min(t + 4, w * SCALE - 2 * s), s)], fill=dash)
        d.line([(s + t, h * SCALE - s), (s + min(t + 4, w * SCALE - 2 * s), h * SCALE - s)], fill=dash)
    for t in range(0, h * SCALE - 2 * s, 8):
        d.line([(s, s + t), (s, s + min(t + 4, h * SCALE - 2 * s))], fill=dash)
        d.line([(w * SCALE - s, s + t), (w * SCALE - s, s + min(t + 4, h * SCALE - 2 * s))], fill=dash)
    rows.append((im, name, f"{w}x{h}", desc))

width = 48 * SCALE + PAD * 3 + LABEL_W
height = sum(r[0].height + PAD for r in rows) + PAD
sheet = Image.new("RGBA", (width, height), (28, 30, 34, 255))
d = ImageDraw.Draw(sheet)
y = PAD
for im, name, size, desc in rows:
    sheet.alpha_composite(im, (PAD, y))
    d.text((PAD + 48 * SCALE + PAD, y + 6), name, fill=(230, 235, 240, 255))
    d.text((PAD + 48 * SCALE + PAD, y + 24), f"{size}  ·  {desc}", fill=(170, 180, 190, 255))
    d.text((PAD + 48 * SCALE + PAD, y + 42), "grid 16px · margin 1px", fill=(120, 130, 140, 255))
    y += im.height + PAD
out = ROOT / "refs" / "spec_canvases.png"
sheet.save(out)
print(out, sheet.size)
