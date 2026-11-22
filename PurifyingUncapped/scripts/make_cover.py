"""把生成的关键图排版成创意工坊封面（1280x720），版式与 Pharmacy 封面保持一致。"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "refs" / "gen"
OUT = ROOT / "mod" / "preview.png"

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
    a = np.clip(0.92 - 0.60 * (x ** 0.75), 0.04, 0.95)[0]
    shade[:, :, 0] = 8
    shade[:, :, 1] = 10
    shade[:, :, 2] = 12
    shade[:, :, 3] = (a * 255).astype(np.uint8)[None, :]
    img = Image.alpha_composite(img, Image.fromarray(shade, "RGBA"))

    # 底部渐隐
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H - 210, H):
        k = (y - (H - 210)) / 210
        gd.line([(0, y), (W, y)], fill=(8, 9, 11, int(185 * k)))
    img = Image.alpha_composite(img, grad)

    d = ImageDraw.Draw(img)
    margin = 78

    d.text((margin, 70), "PROBABLY STOLEN   ·   模组", font=font(FONT_BOLD, 24), fill=ACCENT + (255,))
    d.text((margin - 6, 112), "净化无上限", font=font(FONT_BOLD, 96), fill=TEXT + (255,))
    d.text((margin, 234), "PURIFYING UNCAPPED", font=font(FONT_REG, 30), fill=ACCENT + (255,))
    d.line([(margin, 286), (margin + 620, 286)], fill=(232, 163, 61, 120), width=2)

    lines = [
        "21 级就到顶 95%？",
        "26 级还要 3–4 晚才清得完？",
        "只能靠多摆几台水培机堆吞吐？",
    ]
    y = 324
    for line in lines:
        d.rectangle([margin, y + 10, margin + 9, y + 19], fill=CYAN + (255,))
        d.text((margin + 26, y), line, font=font(FONT_REG, 30), fill=TEXT + (240,))
        y += 52

    d.text((margin, 494), "一晚清掉除矿物质外的一切", font=font(FONT_BOLD, 40), fill=TEXT + (255,))
    d.text((margin, 550), "21 级 98%   ·   22 级起 100%   ·   26 级全清", font=font(FONT_REG, 24), fill=DIM + (255,))

    d.line([(margin, 620), (margin + 620, 620)], fill=(255, 255, 255, 30), width=1)
    d.text((margin, 640), "V1.0.0   ·   净化基因数值补丁   ·   中英双语", font=font(FONT_REG, 22), fill=DIM + (255,))

    # 右下角数据牌：95% -> 100%
    badge_w, badge_h = 232, 132
    bx, by = W - badge_w - 74, H - badge_h - 64
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(
        [bx - 6, by - 6, bx + badge_w + 6, by + badge_h + 6], radius=16, fill=CYAN + (46,)
    )
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(26)))

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=12,
                         fill=(8, 10, 12, 205), outline=(110, 210, 205, 150), width=2)
    img = Image.alpha_composite(img, panel)

    d = ImageDraw.Draw(img)
    f_big = font(FONT_BOLD, 42)
    f_small = font(FONT_REG, 19)
    label = "95% "
    arrow = "→ "
    label2 = "100%"
    w1 = d.textlength(label, font=f_big)
    w2 = d.textlength(arrow, font=f_big)
    w3 = d.textlength(label2, font=f_big)
    total = w1 + w2 + w3
    tx = bx + (badge_w - total) / 2
    ty = by + 26
    d.text((tx, ty), label, font=f_big, fill=DIM + (255,))
    d.text((tx + w1, ty), arrow, font=f_big, fill=ACCENT + (255,))
    d.text((tx + w1 + w2, ty), label2, font=f_big, fill=CYAN + (255,))
    sub = "每晚上限 / PER NIGHT"
    sw = d.textlength(sub, font=f_small)
    d.text((bx + (badge_w - sw) / 2, by + 88), sub, font=f_small, fill=DIM + (235,))

    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)


if __name__ == "__main__":
    cover(sys.argv[1] if len(sys.argv) > 1 else GEN / "keyart.png")
