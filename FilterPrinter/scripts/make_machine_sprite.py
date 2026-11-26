"""Hand-lay the 48x48 sprite for the filter cartridge printer (``fp_printer``).

    python scripts/make_machine_sprite.py [--preview refs/gen/fp_printer_x8.png]

Why this exists: the machine used to borrow the vanilla 3D printer sprite
(``Items/items_tool2`` / ``printer_off``) - the very same image the vanilla 3D printer
uses - so a player running both could not tell the two machines apart at a glance.

**View (1.1.2).** The vanilla machines are not front elevations: they are seen from
slightly above, and their bodies fill the cell edge to edge. Measured off
``refs/vanilla/items_tool2__furnace.png`` (48x48):

* the silhouette is rows 2..46, columns 1..46 - no margin, no feet;
* the top face is a **trapezoid**: row 2 spans 5..42, then each row down widens by 1 px
  per side (4..43, 3..44, 2..45, 1..46), so the surface turns away from the viewer;
* rows 43..46 taper back in the same way (the base recedes);
* both sides carry a 2 px bevel column (lit left, shaded right) and one bright lip
  separates the top face from the front face.

The 1.1.0/1.1.1 sprite was a flat front view with two feet and a 3 px margin, and it read
as a poster rather than a box. This file now follows the vanilla construction: 9 rows of
top face with a **rectangular cartridge hatch** cut into it (dark floor, lit far edge,
three cartridges standing in it with 1 px gaps), and the front panels below.

The hatch is deliberately rectangular, not a tapered trough: a tapered opening with lit
side walls reads as a carry handle at 48 px (the vanilla furnace does have a handle, and
copying that shape onto what is actually an opening was the mistake to avoid).

Colours (12, vanilla machines use 9-12) are sampled from ``items_tool2``: navy
``#292234``, body ``#5f6868``, cream ``#d5d2b8``, teal ``#275654``/``#45918b``, lamps
``#3d823f``/``#9f526d``/``#d5a54a``.

The sprite is 48x48 and the cabinet covers all nine grid-cell centres, so the game
samples 3x3 cells (``GameItem.SetSpriteAndShapeFromMod`` reads the centre pixel of each
cell) - the same footprint as the vanilla printer. Transparency only lives where those
centres are not.
"""

import argparse
import pathlib

W, H = 48, 48

PALETTE = {
    "K": (0x29, 0x22, 0x34),  # navy outline / recess
    "d": (0x36, 0x3F, 0x4A),  # deep shade / screen glass
    "D": (0x3F, 0x4A, 0x52),  # body shadow
    "B": (0x5F, 0x68, 0x68),  # body grey
    "L": (0x88, 0x94, 0x8A),  # lit face (top surface, left bevel)
    "w": (0xA8, 0xAE, 0xA5),  # highlight
    "C": (0xD5, 0xD2, 0xB8),  # cream cartridge
    "T": (0x27, 0x56, 0x54),  # teal shadow
    "t": (0x45, 0x91, 0x8B),  # teal lit
    "g": (0x3D, 0x82, 0x3F),  # LED green
    "a": (0x9F, 0x52, 0x6D),  # LED mauve
    "y": (0xD5, 0xA5, 0x4A),  # LED amber
}

# 顶面与底面的收边：每往下 1 行两侧各放 1 px（照 furnace 量出来的）
TOP_ROWS = ((2, 5, 42), (3, 4, 43), (4, 3, 44), (5, 2, 45))
BOTTOM_ROWS = ((43, 2, 45), (44, 3, 44), (45, 4, 43), (46, 5, 42))
TOP_END = 10          # 顶面最后一行；11 起是正面（含亮唇）
WELL = tuple((y, 13, 34) for y in range(5, 10))
CAPS_ROW = 6          # 滤芯顶盖第一行
CAPS = (15, 21, 27)   # 三支滤芯的左边缘（宽 5 px，缝 1 px）


class Grid:
    def __init__(self, w, h, fill="."):
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
        self.rect(x0, y0, x1, y0, color)
        self.rect(x0, y1, x1, y1, color)
        self.rect(x0, y0, x0, y1, color)
        self.rect(x1, y0, x1, y1, color)

    def hline(self, x0, x1, y, color):
        self.rect(x0, y, x1, y, color)

    def vline(self, x, y0, y1, color):
        self.rect(x, y0, x, y1, color)


def body_mask():
    """原版机器的轮廓：顶面梯形、底部内收、左右顶到 1..46，无脚无留白。"""
    inside = [[False] * W for _ in range(H)]
    for y, l, r in TOP_ROWS:
        for x in range(l, r + 1):
            inside[y][x] = True
    for y in range(6, 43):
        for x in range(1, 47):
            inside[y][x] = True
    for y, l, r in BOTTOM_ROWS:
        for x in range(l, r + 1):
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
            if inside[y][x] and not all(is_in(x + dx, y + dy)
                                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g.put(x, y, "K")

    # 两道倒角：上/左受光 L，下/右背光 D
    for _ in range(2):
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


def top_face(g):
    """顶面：一整块朝上的平面，里面开一个装料井（远壁受光、近壁背光、井底最暗）。"""
    for y in range(2, TOP_END + 1):
        for x in range(W):
            if g.get(x, y) == "B":
                g.put(x, y, "L")
    for x in range(6, 42):                     # 顶面最靠后的一行更亮
        if g.get(x, 2) == "L":
            g.put(x, 2, "w")
    g.hline(4, 43, 3, "D")                     # 顶盖接缝

    # 井：井底最暗（K），远壁受光（D），近沿一条亮边 —— 这样读作"洞"，不是提手
    for y, l, r in WELL:
        g.hline(l, r, y, "K")
    y_back, l_back, r_back = WELL[0]
    g.hline(l_back + 1, r_back - 1, y_back, "D")
    y_front, l_front, r_front = WELL[-1]
    g.hline(l_front - 1, r_front + 1, y_front + 1, "D")  # 舱口在顶面上的投影（光从后上方来）
    g.hline(l_front, r_front, y_front + 2, "w")          # 近沿受光的边
    g.hline(l_front, r_front, TOP_END + 2, "D")       # 洞口投在正面上的影

    # 三支滤芯：几乎填满井口，只在缝隙里露出井底的暗色
    for x0 in CAPS:
        g.put(x0, CAPS_ROW, "d")                       # 圆盖左上角
        g.hline(x0 + 1, x0 + 3, CAPS_ROW, "w")         # 盖顶高光
        g.put(x0 + 4, CAPS_ROW, "d")                   # 圆盖右上角
        g.hline(x0, x0 + 4, CAPS_ROW + 1, "C")         # 筒身
        g.hline(x0, x0 + 4, CAPS_ROW + 2, "T")         # 与井底交界


def front_face(g):
    """正面：亮唇 → 弹匣槽 + 主屏 + 小屏 → 亮唇 → 出料口 + 指示灯 → 散热格栅。"""
    y_face = TOP_END + 1
    g.hline(2, 45, y_face, "w")
    y0 = y_face + 2                            # 13

    # 左侧弹匣槽：竖着三支滤芯
    g.frame(4, y0, 10, y0 + 11, "K")
    g.rect(5, y0 + 1, 9, y0 + 10, "d")
    for k in range(3):
        cy = y0 + 2 + k * 3
        g.rect(6, cy, 8, cy + 2, "C")
        g.hline(6, 8, cy, "w")                 # 顶盖受光
        g.vline(8, cy + 1, cy + 2, "T")        # 右侧背光
        g.hline(6, 8, cy + 2, "T")             # 与槽底交界

    # 主屏（凹进一层，内壁受光/背光）
    g.frame(12, y0, 31, y0 + 12, "K")
    g.hline(13, 30, y0 + 1, "L")
    g.vline(13, y0 + 1, y0 + 11, "L")
    g.vline(30, y0 + 1, y0 + 11, "D")
    g.hline(13, 30, y0 + 11, "D")
    g.rect(14, y0 + 2, 29, y0 + 10, "d")
    funnel = ("tttttttt", "tTTTTTTt", ".tTTTTt.", ".tTTTTt.", "..tTTt..", "..tTTt..", "...tt...")
    for dy, row in enumerate(funnel):
        for dx, ch in enumerate(row):
            if ch != ".":
                g.put(18 + dx, y0 + 2 + dy, ch)
    g.hline(16, 27, y0 + 11, "D")              # 屏幕底部的进度条
    g.hline(16, 20, y0 + 11, "t")

    # 右上小屏 + 青色饰条
    g.frame(34, y0, 42, y0 + 4, "K")
    g.rect(35, y0 + 1, 41, y0 + 3, "d")
    g.hline(35, 41, y0 + 1, "L")
    g.hline(34, 42, y0 + 7, "t")
    g.hline(34, 42, y0 + 8, "T")

    # 下段亮唇
    y_lip = y0 + 14                            # 27
    g.hline(2, 45, y_lip, "w")
    g.hline(2, 45, y_lip + 1, "D")

    # 出料口：横槽里躺着一支滤芯，前沿挡住下半截
    ys = y_lip + 2                             # 29
    g.frame(4, ys, 31, ys + 8, "K")
    g.rect(5, ys + 1, 30, ys + 7, "d")
    g.hline(5, 30, ys + 1, "K")
    g.rect(7, ys + 2, 27, ys + 4, "C")
    g.hline(7, 27, ys + 2, "w")
    g.hline(7, 27, ys + 4, "T")
    g.hline(7, 27, ys + 5, "K")                # 前沿
    g.hline(5, 30, ys + 7, "L")                # 槽底受光

    # 右下指示灯
    g.frame(33, ys, 42, ys + 8, "K")
    g.rect(34, ys + 1, 41, ys + 7, "D")
    for dx, col in ((36, "g"), (38, "y"), (40, "a")):
        g.put(dx, ys + 4, col)

    # 底部散热格栅（原版机器这块是暗色百叶）
    yp = ys + 9                                 # 38
    g.frame(4, yp, 42, 41, "K")
    g.rect(5, yp + 1, 41, 40, "D")
    for x in range(7, 41, 5):
        g.vline(x, yp + 1, 40, "K")

    # 侧壁：左受光、右背光，各补到 2 px
    for y in range(y_face, 42):
        if g.get(2, y) in ("B", "L"):
            g.put(2, y, "L")
        if g.get(3, y) == "B":
            g.put(3, y, "L")
        if g.get(45, y) in ("B", "D"):
            g.put(45, y, "L")          # 右缘受光（渲染图两侧都是亮边）
        if g.get(44, y) == "B":
            g.put(44, y, "L")
        if g.get(43, y) == "B":
            g.put(43, y, "D")          # 再往里一列压暗，读出侧面厚度


def build():
    g = Grid(W, H, ".")
    shell(g)
    top_face(g)
    front_face(g)
    return g


def render(grid):
    from PIL import Image

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for y in range(H):
        for x in range(W):
            key = grid.get(x, y)
            if key == ".":
                continue
            r, g_, b = PALETTE[key]
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
    solid = sum(1 for y in range(H) for x in range(W) if img.getpixel((x, y))[3] > 200)
    colours = len({img.getpixel((x, y)) for y in range(H) for x in range(W)
                   if img.getpixel((x, y))[3] > 200})
    print(f"sprite  {out} ({out.stat().st_size} bytes, {solid} px, {colours} colours)")
    if args.preview:
        p = pathlib.Path(args.preview)
        p.parent.mkdir(parents=True, exist_ok=True)
        zoom(img).save(p)
        print(f"preview {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
