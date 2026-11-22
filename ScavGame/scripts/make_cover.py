"""按「PROBABLY STOLEN」模组封面系列的统一版式，给拾荒手记排版（1280x720）。

系列版式（与滤芯打印机 / 下层药房 / 净化无上限一致）：
  左上 eyebrow → 中文主标题 → 英文副标题 → 分隔线 → 三条要点
  → 粗体卖点 → 细节行 → 分隔线 → 版本页脚
用法：python scripts/make_cover.py [关键图路径]
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_KEYART = ROOT / "art" / "cover_final_a.png"
OUT = ROOT / "mod" / "preview.png"
ALT_OUT = ROOT / "art" / "preview_series.png"

W, H = 1280, 720
ACCENT = (232, 163, 61)
CYAN = (110, 210, 205)
TEXT = (236, 235, 230)
DIM = (150, 152, 150)
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"

TITLE_ZH = "拾荒手记"
TITLE_EN = "SCAVENGER'S NOTES"
BULLETS = [
    "在 24 格里，挑 5–7 次拾取",
    "手电筒 3 次查看 · 放大镜 1 次",
    "受伤可包扎，剩余次数保留",
]
HEADLINE = "不用再受制于运气"
SUB = "舒心拾荒   ·   6×4 网格   ·   中英双语"
FOOTER = "V0.3.0   ·   拾荒小游戏   ·   zh / en"


def font(path, size):
    return ImageFont.truetype(path, size)


def cover(keyart=DEFAULT_KEYART, out=OUT):
    base = Image.open(keyart).convert("RGB")
    if base.size != (W, H):
        base = base.resize((W, H), Image.LANCZOS)
    img = base.convert("RGBA")

    # 左侧压暗，保证文字可读（与其它三个封面同一套曲线）
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
    d.text((margin - 6, 112), TITLE_ZH, font=font(FONT_BOLD, 96), fill=TEXT + (255,))
    d.text((margin, 234), TITLE_EN, font=font(FONT_REG, 30), fill=ACCENT + (255,))
    d.line([(margin, 284), (margin + 600, 284)], fill=(232, 163, 61, 120), width=2)

    y = 322
    for line in BULLETS:
        d.rectangle([margin, y + 10, margin + 9, y + 19], fill=CYAN + (255,))
        d.text((margin + 26, y), line, font=font(FONT_REG, 28), fill=TEXT + (240,))
        y += 50

    d.text((margin, 494), HEADLINE, font=font(FONT_BOLD, 40), fill=TEXT + (255,))
    d.text((margin, 550), SUB, font=font(FONT_REG, 24), fill=DIM + (255,))

    d.line([(margin, 620), (margin + 600, 620)], fill=(255, 255, 255, 30), width=1)
    d.text((margin, 640), FOOTER, font=font(FONT_REG, 22), fill=DIM + (255,))

    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)
    return out


if __name__ == "__main__":
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_KEYART
    cover(src)
    cover(src, ALT_OUT)
