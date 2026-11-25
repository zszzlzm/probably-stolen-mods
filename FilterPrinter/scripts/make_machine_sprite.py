"""Hand-lay the 48x48 sprite for the filter cartridge printer (``fp_printer``).

    python scripts/make_machine_sprite.py [--preview refs/gen/fp_printer_x8.png]

Why this exists: the machine used to borrow the vanilla 3D printer sprite
(``Items/items_tool2`` / ``printer_off``) - the very same image the vanilla 3D printer
uses - so a player running both could not tell the two machines apart at a glance.

Shape reference: the local Qwen-Image model turned an earlier flat draft into
``refs/gen/edit3d_s102.png`` (chamfered lid, open cartridge well on top, inset screen,
output slot with a cartridge, lamps, two feet). That is the silhouette re-drawn here on
the game's 16 px grid - the model's rendering cannot be used directly at 48 px.

Volume rules (what the vanilla machines do and a flat front view does not):

* the cabinet has a **chamfered lid**: the top corners are cut in two 45 deg steps, so
  the top face reads as a surface that turns away from the viewer;
* the top face carries an open **cartridge well**, drawn as a box: far wall ``D``, one
  side wall lit ``L``, the other ``D``, and a bright ``L`` front lip that cuts across the
  three cartridges standing inside - that occluded pixel row is what sells the depth;
* the screen and the output slot are **recessed**: lit inner rim on the top/left, shaded
  rim on the bottom/right, and the front lip of the slot covers the bottom of the
  cartridge lying in it;
* every raised part (well lip, lamp plate, feet) casts a 1 px shadow on the surface
  below it, and the whole shell keeps the vanilla treatment: 2 px black margin, 1 px
  navy border, 1 px ``L`` bevel top/left, 1 px ``D`` bevel bottom/right.

Colours are sampled from ``items_tool2`` (navy ``#292234``, body ``#5f6868``, cream
``#d5d2b8``, teal ``#275654``/``#45918b``, glass ``#4b5b5d``, lamps
``#3d823f``/``#9f526d``/``#d5a54a``) so the machine sits in the same family.

The sprite is 48x48 with all nine grid-cell centres opaque: 3x3 cells at the game's
16 px grid, the same footprint as the vanilla printer.
"""

import argparse
import pathlib

W, H = 48, 48

PALETTE = {
    "E": (0x00, 0x00, 0x00),  # margin
    "K": (0x29, 0x22, 0x34),  # navy outline / recess
    "M": (0x27, 0x34, 0x56),  # dark navy backing
    "m": (0x44, 0x46, 0x4C),  # seam / panel joint
    "B": (0x5F, 0x68, 0x68),  # body grey
    "D": (0x3F, 0x4A, 0x52),  # body shadow
    "d": (0x36, 0x3F, 0x4A),  # deep shade / screen glass
    "L": (0x88, 0x94, 0x8A),  # light bevel
    "w": (0xA8, 0xAE, 0xA5),  # light grey
    "C": (0xD5, 0xD2, 0xB8),  # cream
    "c": (0xB9, 0xB4, 0x9A),  # cream shadow
    "G": (0x4B, 0x5B, 0x5D),  # glass
    "S": (0x80, 0x92, 0x9B),  # glass sheen
    "T": (0x27, 0x56, 0x54),  # teal shadow
    "t": (0x45, 0x91, 0x8B),  # teal lit
    "u": (0x6F, 0xB7, 0xA8),  # teal highlight
    "g": (0x3D, 0x82, 0x3F),  # LED green
    "a": (0x9F, 0x52, 0x6D),  # LED mauve
    "y": (0xD5, 0xA5, 0x4A),  # LED amber
}


class Grid:
    def __init__(self, w, h, fill="E"):
        self.w, self.h = w, h
        self.cells = [[fill] * w for _ in range(h)]

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = color

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.cells[y][x]
        return None

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, color)

    def frame(self, x0, y0, x1, y1, color):
        for x in range(x0, x1 + 1):
            self.put(x, y0, color)
            self.put(x, y1, color)
        for y in range(y0, y1 + 1):
            self.put(x0, y, color)
            self.put(x1, y, color)

    def hline(self, x0, x1, y, color):
        for x in range(x0, x1 + 1):
            self.put(x, y, color)

    def vline(self, x, y0, y1, color):
        for y in range(y0, y1 + 1):
            self.put(x, y, color)


def body_mask():
    """Chamfered cabinet + two feet: True where the machine is."""
    inside = [[False] * W for _ in range(H)]
    # 45 deg chamfer, one step per row, at both top corners
    for y, (left, right) in ((4, (8, 39)), (5, (7, 40)), (6, (6, 41)), (7, (5, 42))):
        for x in range(left, right + 1):
            inside[y][x] = True
    for y in range(8, 43):
        for x in range(3, 45):
            inside[y][x] = True
    for y in (43, 44):
        for x in list(range(9, 13)) + list(range(35, 39)):
            inside[y][x] = True
    return inside


def shell(g):
    inside = body_mask()

    for y in range(H):
        for x in range(W):
            if inside[y][x]:
                g.put(x, y, "B")

    def is_in(x, y):
        return 0 <= x < W and 0 <= y < H and inside[y][x]

    for y in range(H):
        for x in range(W):
            if inside[y][x] and not all(is_in(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g.put(x, y, "K")

    snapshot = [row[:] for row in g.cells]
    for y in range(H):
        for x in range(W):
            if snapshot[y][x] != "B":
                continue
            if y > 0 and snapshot[y - 1][x] == "K":
                g.put(x, y, "L")
            elif y < H - 1 and snapshot[y + 1][x] == "K":
                g.put(x, y, "D")
            elif x > 0 and snapshot[y][x - 1] == "K":
                g.put(x, y, "L")
            elif x < W - 1 and snapshot[y][x + 1] == "K":
                g.put(x, y, "D")


def top_well(g):
    """Open cartridge well on the top face: three cartridges, one clipped by the lip."""
    g.rect(11, 6, 36, 13, "K")                 # well opening
    g.rect(12, 7, 35, 12, "d")                 # dark interior
    g.hline(12, 35, 7, "D")                    # far wall in shade
    g.vline(12, 7, 12, "D")
    g.vline(35, 7, 12, "D")
    g.hline(11, 36, 13, "L")                   # lit front lip of the well
    for x in (14, 20, 26):
        g.rect(x, 8, x + 3, 12, "C")           # cartridge seen from above
        g.hline(x, x + 3, 8, "w")              # lit cap
        g.vline(x, 9, 12, "w")
        g.vline(x + 3, 9, 12, "c")
        g.hline(x, x + 3, 12, "t")             # coupling ring
        g.hline(x, x + 3, 11, "T")
    g.hline(3, 44, 14, "D")                    # shadow the lip drops on the face


def front_face(g):
    # ---- left: narrow cartridge chute ----------------------------------
    g.rect(4, 18, 10, 28, "K")
    g.rect(5, 19, 9, 27, "d")
    g.rect(5, 20, 9, 26, "C")                  # a cartridge standing in the chute
    g.vline(5, 20, 26, "w")
    g.vline(9, 21, 26, "c")
    g.hline(5, 9, 21, "T")                     # coupling ring
    g.hline(5, 9, 22, "t")
    g.hline(4, 10, 24, "K")                    # one retaining bar across the chute
    g.hline(4, 10, 29, "D")                    # shadow under the chute

    # ---- centre: main screen -------------------------------------------
    g.rect(12, 17, 31, 31, "K")
    g.hline(13, 30, 18, "L")                   # lit inner rim, top
    g.vline(13, 18, 30, "L")                   # lit inner rim, left
    g.vline(30, 18, 30, "D")                   # shaded inner rim, right
    g.hline(13, 30, 30, "D")                   # shaded inner rim, bottom
    g.rect(14, 19, 29, 29, "d")                # dark glass
    g.hline(14, 29, 19, "G")
    g.put(15, 20, "S")                         # two sheen pixels, top left
    g.put(16, 20, "S")
    g.put(15, 21, "S")
    funnel = (
        "tttttttt",
        "tTTTTTTt",
        ".tTTTTt.",
        ".tTTTTt.",
        "..tTTt..",
        "..tTTt..",
        "...tt...",
    )
    fx, fy = 18, 21
    for dy, row in enumerate(funnel):
        for dx, ch in enumerate(row):
            if ch != ".":
                g.put(fx + dx, fy + dy, "u" if ch == "t" else "T")
    g.hline(12, 31, 32, "D")                   # shadow under the bezel

    # ---- right: cream label plate + teal strip -------------------------
    g.rect(34, 17, 42, 25, "K")
    g.rect(35, 18, 41, 24, "C")                # raised cream plate
    g.hline(35, 41, 18, "w")                   # lit top face
    g.hline(35, 41, 24, "c")                   # shaded bottom face
    g.hline(36, 40, 20, "D")                   # two engraved lines
    g.hline(36, 40, 22, "D")
    g.hline(34, 42, 27, "t")                   # teal accent below the plate
    g.hline(34, 42, 28, "T")

    # ---- bottom: output slot with a cartridge ---------------------------
    g.hline(3, 44, 33, "D")                    # seam above the slot
    g.rect(4, 34, 31, 41, "K")                 # slot opening
    g.rect(5, 35, 30, 40, "M")                 # dark mouth
    g.hline(5, 30, 35, "K")                    # deep shadow at the top
    g.hline(5, 30, 40, "L")                    # lit slot floor
    g.rect(8, 33, 27, 37, "K")                 # cartridge lying in the slot
    g.rect(9, 34, 26, 36, "C")
    g.hline(9, 26, 34, "L")                    # lit top face
    g.hline(9, 26, 36, "c")
    g.rect(24, 34, 26, 36, "t")                # teal collar at the mouth end
    g.vline(26, 34, 36, "T")
    g.put(9, 35, "w")
    g.hline(9, 27, 38, "K")                    # cast shadow under the cartridge

    # ---- bottom right: indicator lamps ---------------------------------
    g.rect(33, 34, 43, 41, "K")
    g.rect(34, 35, 42, 40, "M")
    g.hline(33, 43, 33, "L")                   # lit top edge of the lamp plate
    g.put(36, 37, "g")
    g.put(38, 37, "y")
    g.put(40, 37, "a")


def build():
    g = Grid(W, H, "E")
    shell(g)
    top_well(g)
    front_face(g)
    return g


def render(grid):
    from PIL import Image

    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            r, g_, b = PALETTE[grid.get(x, y)]
            px[x, y] = (r, g_, b, 255)
    return img


def zoom(img, scale=8, bg=(38, 38, 44, 255)):
    from PIL import Image

    canvas = Image.new("RGBA", (img.width * scale, img.height * scale), bg)
    canvas.alpha_composite(img.resize((img.width * scale, img.height * scale), Image.NEAREST))
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(pathlib.Path(__file__).resolve().parents[1] / "mod" / "Textures" / "Items" / "fp_printer.png"),
    )
    ap.add_argument("--preview", default="")
    args = ap.parse_args()

    img = render(build())
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"sprite  {out} ({out.stat().st_size} bytes)")
    if args.preview:
        p = pathlib.Path(args.preview)
        p.parent.mkdir(parents=True, exist_ok=True)
        zoom(img).save(p)
        print(f"preview {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
