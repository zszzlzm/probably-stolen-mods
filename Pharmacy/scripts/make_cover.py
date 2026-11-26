"""把生成的关键图 + 游戏精灵图 + 标题排版成创意工坊封面（1280x720）。"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "refs" / "gen"
OUT = ROOT / "mod" / "preview.png"

sys.path.insert(0, str(ROOT.parent / "tools"))
from img_fit import cover_fit  # noqa: E402

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
    base = cover_fit(base, (W, H))     # 等比铺满后裁切，不拉伸（3:2 关键图 → 16:9 封面）
    img = base.convert("RGBA")

    # 左侧压暗，保证文字可读
    shade = np.zeros((H, W, 4), np.uint8)
    x = np.linspace(0, 1, W)[None, :]
    a = np.clip(0.90 - 0.62 * (x ** 0.75), 0.04, 0.94)[0]
    shade[:, :, 0] = 10
    shade[:, :, 1] = 11
    shade[:, :, 2] = 14
    shade[:, :, 3] = (a * 255).astype(np.uint8)[None, :]
    img = Image.alpha_composite(img, Image.fromarray(shade, "RGBA"))

    # 底部渐隐
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(H - 200, H):
        k = (y - (H - 200)) / 200
        gd.line([(0, y), (W, y)], fill=(9, 10, 12, int(170 * k)))
    img = Image.alpha_composite(img, grad)

    d = ImageDraw.Draw(img)
    margin = 78

    # 物品图标：右下角摆两件成品（16px 原图 8 倍放大，保持像素感）
    sprite_scale = 8
    vial = Image.open(ROOT / "mod/Textures/Items/calm_agent.png").convert("RGBA")
    pill = Image.open(ROOT / "mod/Textures/Items/painkiller_pill.png").convert("RGBA")
    vial_big = vial.resize((vial.width * sprite_scale, vial.height * sprite_scale), Image.NEAREST)
    pill_big = pill.resize((pill.width * sprite_scale, pill.height * sprite_scale), Image.NEAREST)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gl = ImageDraw.Draw(glow)
    gl.ellipse([930, 470, 1250, 720], fill=ACCENT + (34,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(70)))

    def with_shadow(sprite, pos):
        pad = 26
        shadow = Image.new("RGBA", (sprite.width + pad * 2, sprite.height + pad * 2), (0, 0, 0, 0))
        sil = Image.new("RGBA", sprite.size, (0, 0, 0, 190))
        shadow.paste(sil, (pad, pad), sprite)
        shadow = shadow.filter(ImageFilter.GaussianBlur(9))
        img.alpha_composite(shadow, (pos[0] - pad + 5, pos[1] - pad + 7))
        img.alpha_composite(sprite, pos)

    with_shadow(vial_big, (958, 524))
    with_shadow(pill_big, (1096, 548))

    # 标题区
    d = ImageDraw.Draw(img)
    d.text((margin, 70), "PROBABLY STOLEN   ·   模组", font=font(FONT_BOLD, 24), fill=ACCENT + (255,))
    d.text((margin - 6, 116), "下层药房", font=font(FONT_BOLD, 96), fill=TEXT + (255,))
    d.text((margin, 236), "LOWER-DISTRICT PHARMACY", font=font(FONT_REG, 30), fill=ACCENT + (255,))
    d.line([(margin, 288), (margin + 660, 288)], fill=(232, 163, 61, 120), width=2)

    lines = [
        "违禁品卖得良心不安？",
        "合法药品只有咖啡因片？",
        "原料砸在手里，酒还得自己酿？",
    ]
    y = 326
    for line in lines:
        d.rectangle([margin, y + 10, margin + 9, y + 19], fill=CYAN + (255,))
        d.text((margin + 26, y), line, font=font(FONT_REG, 30), fill=TEXT + (240,))
        y += 52

    d.text((margin, 496), "两种可自制的合法药品", font=font(FONT_BOLD, 40), fill=TEXT + (255,))
    d.text((margin, 552), "澄心剂 0.8ml 梦帽菇萃取液   ·   消痛片 0.08ml 芬太",
           font=font(FONT_REG, 24), fill=DIM + (255,))

    d.line([(margin, 620), (margin + 660, 620)], fill=(255, 255, 255, 30), width=1)
    d.text((margin, 640), "V1.0.0   ·   化学精制机配方   ·   中英双语", font=font(FONT_REG, 22), fill=DIM + (255,))

    img.convert("RGB").save(out, "PNG", optimize=True)
    print("wrote", out, out.stat().st_size, "bytes", img.size)


if __name__ == "__main__":
    cover(sys.argv[1] if len(sys.argv) > 1 else GEN / "keyart.png")
