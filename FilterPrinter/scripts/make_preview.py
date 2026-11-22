#!/usr/bin/env python3
"""生成创意工坊预览图 preview.png（1280x720）。

用法：python scripts/make_preview.py [输出路径]
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
BG_TOP = (20, 23, 28)
BG_BOTTOM = (9, 10, 12)
ACCENT = (232, 163, 61)
ACCENT_DIM = (150, 104, 38)
TEXT = (236, 235, 230)
DIM = (148, 150, 148)

FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def background():
    t = np.linspace(0.0, 1.0, H).reshape(H, 1, 1)
    arr = np.array(BG_TOP, dtype=np.float32) * (1.0 - t) + np.array(BG_BOTTOM, dtype=np.float32) * t
    arr = np.repeat(arr, W, axis=1)
    img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, W, 40):
        gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 6))
    for y in range(0, H, 40):
        gd.line([(0, y), (W, y)], fill=(255, 255, 255, 6))
    img = Image.alpha_composite(img, grid)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_d = ImageDraw.Draw(glow)
    glow_d.ellipse([840, 90, 1300, 640], fill=(232, 163, 61, 26))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    return Image.alpha_composite(img, glow)


def draw_cartridge(img, x, y, w, h):
    """一个风格化的滤芯剪影：外壳 + 栅格 + 接口。"""
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = 40, 40

    body = [ox, oy + 26, ox + w, oy + h - 26]
    d.rounded_rectangle(body, radius=22, fill=(26, 29, 34, 255), outline=ACCENT + (235,), width=5)

    # 顶部接口
    cap_w = int(w * 0.46)
    cap_x = ox + (w - cap_w) // 2
    d.rounded_rectangle([cap_x, oy - 2, cap_x + cap_w, oy + 30], radius=10,
                        fill=(32, 36, 42, 255), outline=ACCENT_DIM + (235,), width=4)
    # 底部出水嘴
    d.rounded_rectangle([ox + w // 2 - 26, oy + h - 44, ox + w // 2 + 26, oy + h - 6], radius=8,
                        fill=(32, 36, 42, 255), outline=ACCENT_DIM + (235,), width=4)

    # 内部栅格
    inner_left, inner_right = ox + 30, ox + w - 30
    top, bottom = oy + 70, oy + h - 92
    rows = 6
    step = (bottom - top) / (rows - 1)
    for i in range(rows):
        yy = int(top + i * step)
        d.line([(inner_left, yy), (inner_right, yy)], fill=ACCENT_DIM + (150,), width=3)
    cols = 4
    cstep = (inner_right - inner_left) / (cols - 1)
    for i in range(cols):
        xx = int(inner_left + i * cstep)
        d.line([(xx, top), (xx, bottom)], fill=ACCENT_DIM + (60,), width=2)

    # 标签条
    d.rounded_rectangle([ox + 26, oy + h - 78, ox + w - 26, oy + h - 54], radius=6,
                        fill=ACCENT + (200,))

    img.alpha_composite(layer, (x - 40, y - 40))


def text(d, xy, s, font, fill, anchor="la"):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mod", "preview.png")

    img = background()

    # 右侧滤芯
    draw_cartridge(img, 950, 150, 210, 430)

    d = ImageDraw.Draw(img)
    margin = 88

    f_tag = load_font(FONT_BOLD, 24)
    f_title = load_font(FONT_BOLD, 104)
    f_sub = load_font(FONT_REG, 30)
    f_bullet = load_font(FONT_REG, 29)
    f_small = load_font(FONT_REG, 23)

    text(d, (margin, 74), "PROBABLY STOLEN   ·   模组", f_tag, ACCENT + (255,))

    title = "滤芯打印机"
    text(d, (margin - 6, 128), title, f_title, TEXT + (255,))
    text(d, (margin, 258), "FILTER CARTRIDGE PRINTER", f_sub, ACCENT + (255,))

    d.line([(margin, 312), (margin + 700, 312)], fill=ACCENT_DIM + (140,), width=2)

    bullets = [
        "自由选择截留物质：重金属 · 微塑料 · 微生物",
        "药物 · 化学品 · 营养物，共 37 种滤芯",
        "打印一次 120 电：电池或电流转换器供电",
        "滤芯耐久 900 · 中英双语界面 zh / en",
    ]
    y = 350
    for line in bullets:
        d.rectangle([margin, y + 9, margin + 9, y + 18], fill=ACCENT + (255,))
        text(d, (margin + 26, y), line, f_bullet, TEXT + (245,))
        y += 56

    d.line([(margin, 620), (margin + 700, 620)], fill=(255, 255, 255, 28), width=1)
    text(d, (margin, 642), "PROBABLY STOLEN  ·  MOD  v1.0.0", f_small, DIM + (255,))

    img = img.convert("RGB")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print("wrote %s (%d bytes, %dx%d)" % (out, os.path.getsize(out), img.width, img.height))


if __name__ == "__main__":
    main()
