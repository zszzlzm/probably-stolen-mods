"""把生成的关键图 + 游戏精灵图排版成创意工坊封面（1280x720）。"""
import os
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "refs" / "gen"
OUT = ROOT / "mod" / "preview.png"
# 游戏素材目录（默认指向本仓库同级的 ScavGame/refs/game，可用 PS_GAME_REFS 覆盖）
GAME = pathlib.Path(os.environ.get("PS_GAME_REFS", ROOT.parent / "ScavGame" / "refs" / "game"))

W, H = 1280, 720
ACCENT = (232, 163, 61)
CYAN = (110, 210, 205)
TEXT = (236, 235, 230)
DIM = (150, 152, 150)
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def cover(keyart, out=OUT):
    base = Image.open(keyart).convert("RGB")
    if base.size != (W, H):
        base = base.resize((W, H), Image.LANCZOS)
    img = base.convert("RGBA")

    # 左侧压暗，保证文字可读
    shade = np.zeros((H, W, 4), np.uint8)
    x = np.linspace(0, 1, W)[None, :]
    a = np.clip(0.93 - 0.58 * (x ** 0.72), 0.04, 0.95)[0]
    shade[:, :, 0] = 8
    shade[:, :, 1] = 10
    shade[:, :, 2] = 12
    shade[:, :, 3] = (a * 255).astype(np.uint8)[None, :]
    img = Image.alpha_composite(img, Image.fromarray(shade, "RGBA"))

    # 底部渐隐
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H - 200, H):
        k = (y - (H - 200)) / 200
        gd.line([(0, y), (W, y)], fill=(8, 9, 11, int(180 * k)))
    img = Image.alpha_composite(img, grad)

    margin = 78
    d = ImageDraw.Draw(img)

    d.text((margin, 70), "PROBABLY STOLEN   ·   模组", font=font(FONT_BOLD, 24), fill=ACCENT + (255,))
    d.text((margin - 6, 112), "滤芯打印机", font=font(FONT_BOLD, 96), fill=TEXT + (255,))
    d.text((margin, 234), "FILTER CARTRIDGE PRINTER", font=font(FONT_REG, 28), fill=ACCENT + (255,))
    d.line([(margin, 284), (margin + 600, 284)], fill=(232, 163, 61, 120), width=2)

    lines = [
        "37 种截留物质，自由选择",
        "重金属 · 微塑料 · 微生物 · 药物",
        "打印一次 120 电，耐久 900",
    ]
    y = 322
    for line in lines:
        d.rectangle([margin, y + 10, margin + 9, y + 19], fill=CYAN + (255,))
        d.text((margin + 26, y), line, font=font(FONT_REG, 28), fill=TEXT + (240,))
        y += 50

    d.text((margin, 494), "想拦什么，就打印什么", font=font(FONT_BOLD, 40), fill=TEXT + (255,))
    d.text((margin, 550), "电池或电流转换器供电   ·   中英双语", font=font(FONT_REG, 24), fill=DIM + (255,))

    d.line([(margin, 620), (margin + 600, 620)], fill=(255, 255, 255, 30), width=1)
    d.text((margin, 640), "V1.0.0   ·   37 种可打印滤芯   ·   zh / en",
           font=font(FONT_REG, 22), fill=DIM + (255,))

    # 关键图里已经有刚打印出来的滤芯，这里不再叠加像素精灵，保持画面干净。

    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)


if __name__ == "__main__":
    cover(sys.argv[1] if len(sys.argv) > 1 else GEN / "keyart.png")
