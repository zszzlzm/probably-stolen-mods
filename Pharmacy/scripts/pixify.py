"""把生成的大图处理成 16x16 的游戏物品图标。

关键点：PIL 直接缩小 RGBA 会让透明像素的颜色渗到边缘（出现色边），
所以先做 alpha 预乘再缩放，最后反预乘。
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

SENTINEL = (1, 2, 3)


def bg_mask(img, tol=30):
    """用泛洪从四角标出背景，返回 bool 数组（True = 背景）。"""
    rgb = img.convert("RGB")
    work = rgb.copy()
    w, h = work.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        try:
            ImageDraw.floodfill(work, seed, SENTINEL, thresh=tol)
        except Exception:
            pass
    arr = np.asarray(work)
    return (arr[:, :, 0] == SENTINEL[0]) & (arr[:, :, 1] == SENTINEL[1]) & (arr[:, :, 2] == SENTINEL[2])


def to_rgba(img, tol=30):
    rgba = img.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32)
    alpha = arr[:, :, 3] / 255.0
    if alpha.min() > 0.98:
        # 没有自带透明通道：用泛洪抠背景
        mask = bg_mask(img, tol)
        alpha = np.where(mask, 0.0, 1.0)
    else:
        alpha = np.where(alpha < 0.04, 0.0, alpha)
    rgb = arr[:, :, :3].copy()
    # 半透明边缘的颜色往往是「物品色 × 背景紫」，直接缩会带紫边：
    # 先把不透明像素的颜色向外扩几圈，填掉过渡带。
    known = alpha >= 0.9
    for _ in range(6):
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(rgb, (dy, dx), (0, 1))
            kshift = np.roll(known, (dy, dx), (0, 1))
            fill = (~known) & kshift
            rgb[fill] = shifted[fill]
            known = known | fill
    out = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _resize_premultiplied(img, size):
    arr = np.asarray(img).astype(np.float32) / 255.0
    a = arr[:, :, 3]
    rgb = arr[:, :, :3] * a[:, :, None]
    chans = []
    for i in range(3):
        ch = Image.fromarray(rgb[:, :, i], "F").resize(size, Image.LANCZOS)
        chans.append(np.asarray(ch))
    al = Image.fromarray(a, "F").resize(size, Image.LANCZOS)
    alpha = np.asarray(al)
    out = np.zeros((size[1], size[0], 4), np.float32)
    safe = np.maximum(alpha, 1e-4)[:, :, None]
    out[:, :, :3] = np.clip(np.dstack(chans) / safe, 0, 1)
    out[:, :, 3] = np.clip(alpha, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def trim(img):
    bbox = img.getchannel("A").getbbox()
    return img.crop(bbox) if bbox else img


def pixify(img, size=16, colors=12, pad=1, alpha_cut=0.35):
    img = trim(to_rgba(img))
    inner = max(1, size - pad * 2)
    scale = inner / max(img.width, img.height)
    w = max(1, round(img.width * scale))
    h = max(1, round(img.height * scale))
    small = _resize_premultiplied(img, (w, h))

    arr = np.asarray(small).astype(np.float32)
    alpha = (arr[:, :, 3] / 255.0 >= alpha_cut).astype(np.uint8) * 255
    rgb = Image.fromarray(arr[:, :, :3].astype(np.uint8), "RGB")
    q = rgb.quantize(colors=colors, method=Image.FASTOCTREE, dither=Image.NONE).convert("RGB")
    q.putalpha(Image.fromarray(alpha, "L"))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(q, ((size - w) // 2, (size - h) // 2))
    return canvas


def preview(sprite, scale=16, bg=(38, 38, 44, 255)):
    img = Image.new("RGBA", (sprite.width * scale, sprite.height * scale), bg)
    img.alpha_composite(sprite.resize((sprite.width * scale, sprite.height * scale), Image.NEAREST))
    return img


if __name__ == "__main__":
    import pathlib

    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.stem + "_16.png")
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    sprite = pixify(Image.open(src), size=size)
    sprite.save(out)
    preview(sprite).save(out.with_name(out.stem + "_preview.png"))
    print("wrote", out, sprite.size)


def add_outline(sprite, color=(26, 30, 44), diagonal=False):
    """给剪影补一圈深色描边（放在透明像素上，不覆盖原图像素）。"""
    import numpy as _np

    arr = _np.asarray(sprite).astype(_np.uint8).copy()
    opaque = arr[:, :, 3] > 0
    neigh = _np.zeros_like(opaque)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)) + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else ()):
        neigh |= _np.roll(opaque, (dy, dx), (0, 1))
    ring = neigh & (~opaque)
    arr[ring] = [color[0], color[1], color[2], 255]
    return Image.fromarray(arr, "RGBA")


def clean_alpha(sprite, keep=4, grow=6):
    """3x3 邻域投票修形：去掉毛刺/孤立像素，补上凹陷，让 16px 的剪影更规整。"""
    from numpy.lib.stride_tricks import sliding_window_view

    arr = np.asarray(sprite).astype(np.uint8).copy()
    a = arr[:, :, 3] > 0
    win = sliding_window_view(np.pad(a.astype(np.uint8), 1), (3, 3))
    cnt = win.sum(axis=(2, 3))
    solid = np.where(a, cnt >= keep, cnt >= grow)
    out = arr.copy()
    out[~solid] = 0
    # 新补上的像素借邻居颜色
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        need = solid & (out[:, :, 3] == 0)
        src = np.roll(out, (dy, dx), (0, 1))
        out[need] = src[need]
    return Image.fromarray(out, "RGBA")
