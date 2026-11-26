"""把生成的关键图排版成创意工坊封面（1280x720），沿用系列版式。

用法：python scripts/make_cover.py [关键图路径] [输出路径] [--zoom=1.0] [--dx=0] [--dy=0]
默认：refs/gen/keyart_shift2.png -> mod/preview.png（另出一张 640x360 到 build/preview_640.png）

--zoom / --dx / --dy 是「重新构图」：先按 zoom 裁一刀再缩回 1280x720，dx/dy 是裁切窗口的像素偏移。
当前封面用的是已经重新构过图的关键图 refs/gen/keyart_shift2.png（zoom 1.10 + 右移），所以默认参数即可复现；
下一张图可以直接用 --zoom/--dx/--dy 一步到位，不必再手搓中间文件。
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = ROOT / "refs" / "gen"
OUT = ROOT / "mod" / "preview.png"
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

TITLE = "更好的奥克莫吸注射器"
SUBTITLE = "BETTER LUXURY NOMORE INJECTOR"
BULLETS = [
    "添加「奢侈品」类型：收藏家与上层客人会购买",
    "基础价值 50 → 350，与赛纳普斯注射器同档",
    "原版物品，不改配方、不新增任何物品",
]
SELL = "让好药值得做"
DETAIL = "一个 Harmony 补丁   ·   无能力声明"
FOOTER = "V1.0.0   ·   奥克莫吸注射器   ·   zh / en"


def font(path, size):
    return ImageFont.truetype(path, size)


def reframe(base, zoom=1.0, dx=0, dy=0):
    """裁一刀再缩放：zoom>1 放大主体，dx/dy 平移构图（单位是 1280x720 上的像素）。"""
    if zoom == 1.0 and dx == 0 and dy == 0:
        return base
    bw, bh = base.size
    cw, ch = int(round(bw / zoom)), int(round(bh / zoom))
    left = max(0, min(bw - cw, (bw - cw) // 2 + dx))
    top = max(0, min(bh - ch, (bh - ch) // 2 + dy))
    return base.crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)


def cover(keyart, out=OUT, zoom=1.0, dx=0, dy=0):
    base = Image.open(keyart).convert("RGB")
    base = cover_fit(base, (W, H))     # 等比铺满后裁切，不拉伸（3:2 关键图 → 16:9 封面）
    base = reframe(base, zoom, dx, dy)
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

    small_path = ROOT / "build" / "preview_640.png"
    small_path.parent.mkdir(parents=True, exist_ok=True)
    small = img.convert("RGB").resize(SMALL_SIZE, Image.LANCZOS)
    small.save(small_path, "PNG", optimize=True)
    print("wrote", small_path, small_path.stat().st_size, "bytes", small.size)


if __name__ == "__main__":
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--"))
    keyart = pathlib.Path(positional[0]) if len(positional) > 0 else GEN / "keyart_shift2.png"
    out = pathlib.Path(positional[1]) if len(positional) > 1 else OUT
    cover(
        keyart,
        out,
        zoom=float(flags.get("zoom", 1.0)),
        dx=int(flags.get("dx", 0)),
        dy=int(flags.get("dy", 0)),
    )
