"""把生成的关键图排版成创意工坊封面（1280x720），沿用系列版式。

用法：python scripts/make_cover.py [关键图路径] [输出路径]
默认：refs/gen/keyart.png -> mod/preview.png
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "refs" / "gen"
OUT = ROOT / "mod" / "preview.png"
# 包内用的小图：工坊条目的 file_size 只统计 contentfolder，把 1280 的封面塞进去会白白多 0.7 MB。
SMALL = ROOT / "build" / "preview_640.png"
SMALL_SIZE = (640, 360)

sys.path.insert(0, str(ROOT.parent / "tools"))
from img_fit import cover_fit  # noqa: E402

W, H = 1280, 720
ACCENT = (232, 163, 61)
CYAN = (110, 210, 205)
TEXT = (236, 235, 230)
DIM = (150, 152, 150)
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"

TITLE = "还原蕨"
SUBTITLE = "REDUCTION FERN"
BULLETS = [
    "新作物：孢子 → 蕨叶 → 还原剂",
    "一株自给 · 孢子与叶片全部合法",
    "标准叶 120 ml 一茬 · 满血大叶 190 ml",
]
SELL = "还原剂，从田里长出来"
DETAIL = "网络解锁 450 信用点   ·   中英双语"
FOOTER = "V0.1.0   ·   水培作物   ·   zh / en"


def font(path, size):
    return ImageFont.truetype(path, size)


def cover(keyart, out=OUT):
    base = Image.open(keyart).convert("RGB")
    base = cover_fit(base, (W, H))     # 等比铺满后裁切，不拉伸（3:2 关键图 → 16:9 封面）
    img = base.convert("RGBA")

    # 左侧压暗，保证文字可读（系列统一曲线）
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

    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)

    small = img.convert("RGB").resize(SMALL_SIZE, Image.LANCZOS)
    small_path = out.parent.parent / "build" / "preview_640.png"
    small_path.parent.mkdir(parents=True, exist_ok=True)
    small.save(small_path, "PNG", optimize=True)
    print("wrote", small_path, small_path.stat().st_size, "bytes", small.size)


if __name__ == "__main__":
    keyart = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else GEN / "keyart.png"
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    cover(keyart, out)
