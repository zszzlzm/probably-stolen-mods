"""Try a few procedural fiddlehead parameters and show them side by side at 16x16."""
import math
import pathlib

from PIL import Image, ImageDraw

OUT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "hand"
VARIANTS = [
    # (turns, start_angle_deg, r0, r1, width, threshold)
    (1.8, 90, 0.34, 0.10, 0.11, 0.40),
    (2.0, 90, 0.36, 0.08, 0.10, 0.40),
    (1.6, 120, 0.32, 0.12, 0.13, 0.45),
    (2.2, 90, 0.38, 0.06, 0.09, 0.45),
    (1.9, 60, 0.33, 0.10, 0.12, 0.42),
    (1.7, 150, 0.30, 0.14, 0.14, 0.42),
]


def render(turns, ang, r0, r1, width, thr, N=128, S=8):
    mask = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(mask)
    cx, cy = N * 0.5, N * 0.52
    pts = []
    steps = 260
    for i in range(steps + 1):
        t = i / steps
        th = math.radians(ang) + t * turns * 2 * math.pi
        r = N * (r0 + (r1 - r0) * t)
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    d.line(pts, fill=255, width=int(N * width), joint="curve")

    cells = []
    for gy in range(16):
        row = []
        for gx in range(16):
            filled = 0
            for sy in range(S):
                for sx in range(S):
                    if mask.getpixel((gx * S + sx, gy * S + sy)) > 127:
                        filled += 1
            row.append(filled >= S * S * thr)
        cells.append(row)
    return cells


def to_img(cells):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 3))
    for y in range(16):
        for x in range(16):
            if cells[y][x]:
                im.putpixel((x, y), (0x8A, 0xBF, 0xBB, 255))
    return im


cells_list = [render(*v) for v in VARIANTS]
sheet = Image.new("RGBA", (6 * (16 * 8 + 8) + 8, 16 * 8 + 40), (26, 28, 32, 255))
d = ImageDraw.Draw(sheet)
for i, cells in enumerate(cells_list):
    im = to_img(cells).resize((128, 128), Image.NEAREST)
    sheet.alpha_composite(im, (8 + i * 136, 8))
    d.text((8 + i * 136, 144), f"v{i}", fill=(210, 220, 230))
out = OUT / "fern_s_variants.png"
sheet.save(out)
print(out)
