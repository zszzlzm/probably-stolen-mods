"""生成试剂可售的工坊封面（1280x720）+ 包内小图（640x360）。

封面完全由代码绘制：深色台面、四只像素试剂瓶、贴在瓶身上的价格签，和模组本身的像素调性一致。
不用生图模型，也不引用原版美术资源。

用法：python scripts/make_cover.py [输出路径]
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "mod" / "preview.png"
SMALL = ROOT / "build" / "preview_640.png"
SMALL_SIZE = (640, 360)

W, H = 1280, 720
COUNTER_Y = 566

# 与模组/原版机器贴图同一套色板
INK = (24, 20, 28)
GLASS_DARK = (58, 70, 74)
GLASS_MID = (96, 110, 108)
GLASS_HI = (170, 180, 172)
CAP = (54, 63, 74)
CAP_HI = (95, 104, 104)
CREAM = (213, 210, 184)
TEAL = (63, 132, 128)
ACID = (61, 130, 63)
VIOLET = (150, 74, 100)
AMBER = (198, 150, 66)

TEXT = (238, 237, 232)
DIM = (152, 154, 152)
ACCENT = (232, 163, 61)
CYAN = (110, 210, 205)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"

TITLE = "试剂可售"
SUBTITLE = "REAGENT RESALE"
BULLETS = [
    "拆包后的酸碱醇试剂可以卖了",
    "按水价计价：250 ml 试剂 ≈ 13 信用点",
    "原版把非水液体判成沟渠水 −90%，已修正",
]
SELL = "拆错的包，不再是纯亏"
DETAIL = "兼容 0.46D   ·   不改存档结构   ·   中英双语"
FOOTER = "V1.0.0   ·   交易与定价   ·   zh / en"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


class Sprite:
    """16x32 的像素画布，坐标左上为原点。"""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[(0, 0, 0, 0)] * w for _ in range(h)]

    def put(self, x, y, color, a=255):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = tuple(color) + (a,)

    def rect(self, x0, y0, x1, y1, color, a=255):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, color, a)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h))
        im.putdata([self.px[y][x] for y in range(self.h) for x in range(self.w)])
        return im


def bottle(liquid, fill=0.72, label=True):
    """一只 16x32 的试剂瓶：瓶盖、长颈、斜肩、玻璃瓶身、液体、纸质标签。"""

    def shade(c, d):
        return tuple(max(0, min(255, v + d)) for v in c)

    s = Sprite(16, 32)

    def half_at(y):
        if y <= 8:
            return None          # 颈部，单独画
        if y == 9:
            return 4
        if y == 10:
            return 5
        return 6

    # 瓶身
    for y in range(9, 30):
        h = half_at(y)
        s.rect(8 - h, y, 7 + h, y, GLASS_MID)
    # 玻璃质感
    for y in range(9, 30):
        h = half_at(y)
        s.put(8 - h + 1, y, GLASS_HI)
        s.put(7 + h, y, shade(GLASS_MID, -26))
        s.put(7 + h - 1, y, shade(GLASS_MID, -12))

    # 液体（先画，标签压在上面）
    top = int(28 - (28 - 16) * fill)
    for y in range(top, 29):
        h = half_at(y)
        s.rect(8 - h + 1, y, 7 + h - 2, y, liquid)
    s.rect(3, top, 11, top, shade(liquid, 50))
    s.rect(3, 28, 11, 28, shade(liquid, -40))

    # 纸质标签
    if label:
        s.rect(3, 13, 12, 20, CREAM)
        s.rect(3, 13, 12, 13, shade(CREAM, 20))
        s.rect(3, 20, 12, 20, shade(CREAM, -18))
        s.rect(5, 15, 11, 15, INK, 170)
        s.rect(5, 17, 9, 17, INK, 90)
        s.rect(5, 19, 11, 19, ACCENT, 150)

    # 颈 + 盖
    s.rect(6, 5, 9, 8, GLASS_MID)
    s.rect(6, 5, 6, 8, GLASS_HI)
    s.rect(4, 4, 11, 4, CAP)
    s.rect(5, 1, 10, 3, CAP)
    s.rect(6, 1, 9, 1, CAP_HI)

    # 描边
    for y in range(9, 30):
        h = half_at(y)
        s.put(8 - h, y, INK)
        s.put(7 + h, y, INK)
    for x in range(4, 12):
        s.put(x, 9, INK)
    s.put(6, 8, INK)
    s.put(9, 8, INK)
    s.put(4, 4, INK)
    s.put(11, 4, INK)
    s.put(5, 3, INK)
    s.put(10, 3, INK)

    # 落地阴影
    s.rect(3, 30, 12, 30, INK, 80)
    return s.image()


def backdrop():
    y = np.linspace(0, 1, H)[:, None]
    base = np.zeros((H, W, 3), np.float64)
    for i, (top, bot) in enumerate(zip((20, 23, 27), (7, 8, 10))):
        base[:, :, i] = top + (bot - top) * (y ** 0.8)
    img = Image.fromarray(base.astype(np.uint8), "RGB").convert("RGBA")

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r, a in ((520, 14), (400, 18), (290, 22), (190, 24)):
        gd.ellipse([930 - r, 420 - r, 930 + r, 420 + r], fill=(70, 150, 145, a))
    img = Image.alpha_composite(img, glow)

    counter = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(counter)
    cd.rectangle([0, COUNTER_Y, W, H], fill=(24, 27, 30, 255))
    cd.line([(0, COUNTER_Y - 2), (W, COUNTER_Y - 2)], fill=(130, 140, 136, 90), width=2)
    cd.line([(0, COUNTER_Y), (W, COUNTER_Y)], fill=(9, 10, 12, 230), width=2)
    img = Image.alpha_composite(img, counter)
    return img


def paste(img, layer, center_x, baseline, scale, fade=None, max_alpha=1.0):
    big = layer.resize((layer.width * scale, layer.height * scale), Image.NEAREST)
    if fade is not None:
        alpha = np.array(big.getchannel("A"), np.float64)
        ramp = max_alpha * (np.linspace(1.0, 0.0, big.height)[:, None] ** fade)
        big.putalpha(Image.fromarray((alpha * ramp).astype(np.uint8)))
    img.alpha_composite(big, (int(center_x - big.width / 2), int(baseline - big.height)))
    return big


def sticker(text, sub):
    """贴在瓶身上的价格签（略微旋转）。"""
    w, h = 176, 68
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=7, fill=CREAM + (255,))
    d.rounded_rectangle([7, 7, w - 8, h - 8], radius=5, outline=(150, 146, 126, 255), width=1)
    d.text((17, 6), text, font=font(FONT_BOLD, 36), fill=(46, 38, 30, 255))
    d.text((106, 12), sub, font=font(FONT_BOLD, 19), fill=(46, 38, 30, 255))
    d.text((106, 37), "250 ml", font=font(FONT_REG, 15), fill=(96, 86, 68, 255))
    return im.rotate(6, resample=Image.NEAREST, expand=True)


def cover(out=OUT):
    img = backdrop()

    bottles = [
        (bottle(ACID, 0.82), 700, 8),
        (bottle(TEAL, 0.60), 830, 8),
        (bottle(AMBER, 0.92), 960, 8),
        (bottle(VIOLET, 0.70), 1090, 8),
    ]
    for sprite, cx, scale in bottles:
        flipped = sprite.crop((0, 15, sprite.width, sprite.height)).transpose(Image.FLIP_TOP_BOTTOM)
        paste(img, flipped, cx, COUNTER_Y + flipped.height * scale, scale, fade=1.6, max_alpha=0.26)
        paste(img, sprite, cx, COUNTER_Y, scale)

    tag = sticker("13", "CR")
    img.alpha_composite(tag, (756, 588))

    # 左侧压暗，保证标题可读
    shade = np.zeros((H, W, 4), np.uint8)
    x = np.linspace(0, 1, W)[None, :]
    a = np.clip(0.93 - 0.58 * (x ** 0.72), 0.05, 0.95)[0]
    shade[:, :, 0] = 8
    shade[:, :, 1] = 10
    shade[:, :, 2] = 12
    shade[:, :, 3] = (a * 255).astype(np.uint8)[None, :]
    img = Image.alpha_composite(img, Image.fromarray(shade, "RGBA"))

    d = ImageDraw.Draw(img)
    margin = 78
    d.text((margin, 70), "PROBABLY STOLEN   ·   模组", font=font(FONT_BOLD, 24), fill=ACCENT + (255,))
    d.text((margin - 6, 112), TITLE, font=font(FONT_BOLD, 96), fill=TEXT + (255,))
    d.text((margin, 234), SUBTITLE, font=font(FONT_REG, 28), fill=ACCENT + (255,))
    d.line([(margin, 284), (margin + 600, 284)], fill=(232, 163, 61, 120), width=2)

    y = 322
    for line in BULLETS:
        d.rectangle([margin, y + 10, margin + 9, y + 19], fill=CYAN + (255,))
        d.text((margin + 26, y), line, font=font(FONT_REG, 28), fill=TEXT + (240,))
        y += 50

    d.text((margin, 494), SELL, font=font(FONT_BOLD, 40), fill=TEXT + (255,))
    d.text((margin, 550), DETAIL, font=font(FONT_REG, 24), fill=DIM + (255,))

    d.line([(margin, 620), (margin + 600, 620)], fill=(255, 255, 255, 30), width=1)
    d.text((margin, 640), FOOTER, font=font(FONT_REG, 22), fill=DIM + (255,))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)

    small = img.convert("RGB").resize(SMALL_SIZE, Image.LANCZOS)
    SMALL.parent.mkdir(parents=True, exist_ok=True)
    small.save(SMALL, "PNG", optimize=True)
    print("wrote", SMALL, SMALL.stat().st_size, "bytes", small.size)


if __name__ == "__main__":
    cover(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
