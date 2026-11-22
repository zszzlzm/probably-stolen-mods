"""Hand-lay the mod sprites on the exact vanilla pixel grid.

Shapes follow the model-generated candidates; pixels are re-laid at 16x16 / 16x32 /
32x32 / 48x64 using only colors from the vanilla plant palette, with the same
margin and the same (0, 0, 0, 3) background filler the vanilla sprites use.
"""
import pathlib

from PIL import Image

OUT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "hand"
OUT.mkdir(parents=True, exist_ok=True)

PALETTE = {
    ".": (0, 0, 0, 0),
    "K": (0x29, 0x22, 0x34, 255),  # outline
    "D": (0x27, 0x56, 0x54, 255),  # dark teal shade
    "T": (0x2F, 0x75, 0x6F, 255),  # teal
    "B": (0x45, 0x91, 0x8B, 255),  # bright teal
    "L": (0x8A, 0xBF, 0xBB, 255),  # pale teal
    "G": (0x3D, 0x82, 0x3F, 255),  # leaf green
    "g": (0x41, 0x60, 0x3F, 255),  # dark green
    "C": (0xC5, 0xAC, 0x96, 255),  # cream stem
    "M": (0x7D, 0x4F, 0x4A, 255),  # brown
    "m": (0xA4, 0x71, 0x5D, 255),  # light brown
    "r": (0xB6, 0x8B, 0x74, 255),  # tan
    "w": (0xD5, 0xD2, 0xB8, 255),  # off-white label
}


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [["." for _ in range(w)] for _ in range(h)]

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return "."

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def outline(self, color="K"):
        """Add an outline on pixels that are empty and touch the silhouette (4-neigh)."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] != ".":
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c = self.get(x + dx, y + dy)
                    if c not in (".",):
                        add.append((x, y))
                        break
        for x, y in add:
            self.put(x, y, color)

    def image(self, filler=(0, 0, 0, 3)):
        img = Image.new("RGBA", (self.w, self.h), filler)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c != ".":
                    img.putpixel((x, y), PALETTE[c])
        return img


def frond(cv, base_x, top_y, height, leaf_pairs, stem="T", vein="L",
          leaf="G", dark="g", lean=0, leaf_len=2, step=3):
    """Draw one upright fern frond: stem + alternating leaflet pairs."""
    bottom = top_y + height
    for i in range(height + 1):
        y = top_y + i
        t = i / max(1, height)
        x = base_x + round(lean * t * t)
        cv.put(x, y, stem)
        if i % 2 == 0 and i < height - 2:
            cv.put(x, y, vein)
    # leaflets alternate along the stem
    for k in range(leaf_pairs):
        y = top_y + 2 + k * step
        if y >= bottom - 2:
            break
        t = (y - top_y) / max(1, height)
        x = base_x + round(lean * t * t)
        # right leaflet
        cv.put(x + 1, y, leaf)
        cv.put(x + 2, y - 1, leaf)
        if leaf_len >= 3:
            cv.put(x + 3, y - 1, leaf)
        # left leaflet
        cv.put(x - 1, y, leaf)
        cv.put(x - 2, y - 1, leaf)
        if leaf_len >= 3:
            cv.put(x - 3, y - 1, leaf)
        # shaded underside
        cv.put(x + 1, y + 1, dark)
        cv.put(x - 1, y + 1, dark)


def make_fern():
    cv = Canvas(16, 32)
    frond(cv, 6, 3, 25, 7, lean=0)
    frond(cv, 3, 9, 20, 6, lean=-1)
    frond(cv, 11, 10, 19, 6, lean=1)
    # roots / base
    cv.rect(6, 29, 2, 2, "D")
    cv.rect(5, 30, 4, 1, "D")
    cv.outline()
    return cv


def make_fern_l():
    cv = Canvas(32, 32)
    frond(cv, 15, 2, 27, 8, lean=0, leaf_len=3)
    frond(cv, 10, 6, 23, 7, lean=-2, leaf_len=3)
    frond(cv, 20, 6, 23, 7, lean=2, leaf_len=3)
    frond(cv, 5, 12, 17, 6, lean=-3, leaf_len=2)
    frond(cv, 25, 12, 17, 6, lean=3, leaf_len=2)
    cv.rect(14, 28, 4, 2, "D")
    cv.rect(12, 30, 8, 1, "D")
    cv.outline()
    return cv


def make_fern_s():
    """Fiddlehead: a thick spiral drawn at 4x, then snapped to the 16x16 grid."""
    from PIL import ImageDraw as _ImageDraw
    import math

    S = 4
    N = 16 * S
    mask = Image.new("L", (N, N), 0)
    d = _ImageDraw.Draw(mask)
    cx, cy = N * 0.5, N * 0.56
    pts = []
    turns = 1.65
    steps = 220
    for i in range(steps + 1):
        t = i / steps
        theta = t * turns * 2 * math.pi
        r = (N * 0.30) * (1 - 0.62 * t)
        x = cx + r * math.cos(theta + math.pi * 0.5)
        y = cy + r * math.sin(theta + math.pi * 0.5)
        pts.append((x, y))
    d.line(pts, fill=255, width=int(N * 0.13), joint="curve")

    cells = []
    for gy in range(16):
        row = []
        for gx in range(16):
            filled = 0
            for sy in range(S):
                for sx in range(S):
                    if mask.getpixel((gx * S + sx, gy * S + sy)) > 127:
                        filled += 1
            row.append(filled >= (S * S) * 0.42)
        cells.append(row)

    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            if cells[y][x]:
                cv.put(x, y, "L" if (x + y) < 15 else "T")
    # a little dark shading on the inner/underside of the tube
    for y in range(16):
        for x in range(16):
            if cv.get(x, y) in ("T",) and (x + y) > 17:
                cv.put(x, y, "D")
    cv.outline()
    return cv


SEED_ROWS = [
    "................",
    ".KKKKKKKKKKKKKK.",
    ".KwCwCwCwCwwwwK.",
    ".KMMMMMrrrMMMMK.",
    "..KMrCwwwwCrMK..",
    "..KrwwwwwwwwrK..",
    "..KCwwwwwwwwCK..",
    "..KCwwwwwwwwCK..",
    "..KCwwwwwwwwCK..",
    "..KCwwwwwwwwCK..",
    "..KCwwwwwwwwCK..",
    "..KrCwwwwwwrMK..",
    "..KMMMMMMMMMMK..",
    ".KMrrrrrrrrrrMK.",
    ".KKKKKKKKKKKKKK.",
    "................",
]


def make_seed():
    cv = Canvas(16, 16)
    for y, row in enumerate(SEED_ROWS):
        for x, ch in enumerate(row):
            cv.put(x, y, ch)
    # fern glyph, 5 px wide, stamped in the label area
    glyph = {
        (7, 5): "B",
        (6, 6): "B", (7, 6): "T", (8, 6): "B",
        (5, 7): "G", (6, 7): "T", (7, 7): "T", (8, 7): "T", (9, 7): "G",
        (6, 8): "B", (7, 8): "T", (8, 8): "B",
        (5, 9): "G", (6, 9): "T", (7, 9): "T", (8, 9): "T", (9, 9): "G",
        (6, 10): "B", (7, 10): "T", (8, 10): "B",
        (7, 11): "T",
    }
    for (x, y), ch in glyph.items():
        cv.put(x, y, ch)
    return cv


def make_plant_p():
    cv = Canvas(48, 64)
    # tray
    cv.rect(6, 50, 36, 4, "M")
    cv.rect(6, 50, 36, 1, "D")
    cv.rect(8, 54, 32, 8, "K")
    cv.rect(9, 55, 30, 6, "D")
    # water glints
    cv.rect(12, 56, 6, 1, "T")
    cv.rect(28, 57, 8, 1, "B")
    cv.rect(20, 58, 4, 1, "T")
    # young fronds, growing upward
    frond(cv, 16, 30, 20, 6, lean=-2, leaf_len=2, stem="T", vein="L")
    frond(cv, 24, 28, 22, 6, lean=0, leaf_len=2, stem="T", vein="L")
    frond(cv, 32, 30, 20, 6, lean=2, leaf_len=2, stem="T", vein="L")
    frond(cv, 11, 36, 14, 4, lean=-3, leaf_len=2, stem="T", vein="L")
    frond(cv, 37, 36, 14, 4, lean=3, leaf_len=2, stem="T", vein="L")
    cv.outline()
    return cv


def main():
    specs = {
        "restoring_fern": (make_fern(), 12),
        "restoring_fern_s": (make_fern_s(), 12),
        "restoring_fern_l": (make_fern_l(), 8),
        "restoring_fern_seed": (make_seed(), 12),
        "restoring_fern_p": (make_plant_p(), 6),
    }
    for name, (cv, scale) in specs.items():
        img = cv.image()
        path = OUT / f"{name}.png"
        img.save(path)
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        bg = Image.new("RGBA", big.size, (30, 32, 36, 255))
        for y in range(0, big.height, 8):
            for x in range(0, big.width, 8):
                if (x // 8 + y // 8) % 2:
                    bg.paste((38, 40, 46, 255), (x, y, min(x + 8, big.width), min(y + 8, big.height)))
        bg.alpha_composite(big)
        bg.save(OUT / f"{name}_x{scale}.png")
        print(name, img.size)


if __name__ == "__main__":
    main()
