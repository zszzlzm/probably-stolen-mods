"""`tools/img_fit.cover_fit` 的几何自检（不联网、不碰游戏文件）。

    python tools/test_img_fit.py

为什么要有：封面按文档配方要在 1536×1024 生成，再裁成 1280×720。
早先的脚本直接 `resize((1280, 720))`，会把 3:2 压扁成 16:9（横向拉伸约 18%）。
这个自检保证「等比裁切、不拉伸」，改 `cover_fit` 时先跑它。
"""
import pathlib
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from img_fit import cover_fit  # noqa: E402

CHECKS = 0


def check(name, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if not cond:
        raise SystemExit(f"FAIL {name} {detail}")
    print(f"ok {name} {detail}".rstrip())


def square_size(img):
    red = [(x, y) for x in range(img.width) for y in range(img.height)
           if img.getpixel((x, y))[:3] == (255, 0, 0)]
    xs = [p[0] for p in red]
    ys = [p[1] for p in red]
    return max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def main():
    # 1) 同尺寸输入：原样返回，老封面重跑不变
    same = Image.new("RGB", (1280, 720), (10, 10, 10))
    out = cover_fit(same, (1280, 720))
    check("identity size", out.size == (1280, 720), str(out.size))
    check("identity pixels", out.getpixel((5, 5)) == (10, 10, 10))

    # 2) 3:2 输入：输出必须是 16:9，且居中的正方形还是正方形（说明是裁切不是拉伸）
    im = Image.new("RGB", (1536, 1024), (30, 30, 40))
    ImageDraw.Draw(im).rectangle([640, 384, 895, 639], fill=(255, 0, 0))
    out = cover_fit(im, (1280, 720))
    check("crop size", out.size == (1280, 720), str(out.size))
    w, h = square_size(out)
    check("no stretch", abs(w - h) <= 1, f"{w}x{h}")

    # 3) 极窄输入：仍然铺满，不留黑边
    tall = Image.new("RGB", (400, 2000), (0, 0, 255))
    out = cover_fit(tall, (1280, 720))
    check("tall fills", out.getpixel((0, 0)) == (0, 0, 255) and out.getpixel((1279, 719)) == (0, 0, 255))

    # 4) zoom/dx/dy 不越界
    im = Image.new("RGB", (1536, 1024), (40, 40, 40))
    for zoom, dx, dy in ((1.5, 0, 0), (1.0, 9999, -9999), (0.1, 0, 0)):
        o = cover_fit(im, (1280, 720), zoom=zoom, dx=dx, dy=dy)
        check(f"zoom={zoom} dx={dx} dy={dy} size", o.size == (1280, 720), str(o.size))

    print(f"\n{CHECKS} checks passed")


if __name__ == "__main__":
    raise SystemExit(main())
