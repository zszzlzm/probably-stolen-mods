"""等比裁切：把任意尺寸的图铺满目标画幅，不拉伸。

为什么需要：封面按文档要生成 1536×1024（3:2），而工坊要 1280×720（16:9）。
早先的 `make_cover.py` 直接 `resize((1280, 720))`，等于把 3:2 压扁 18%；
生成尺寸一改就会变形。这里统一成「按长边放大铺满 → 居中裁切」。

`zoom` 在铺满之后再放大（>1 等于裁得更紧），`dx/dy` 平移裁切窗（像素，目标坐标系）。
"""
from __future__ import annotations

from PIL import Image

__all__ = ["cover_fit"]


def cover_fit(img: Image.Image, size: tuple[int, int] = (1280, 720), zoom: float = 1.0,
              dx: int = 0, dy: int = 0) -> Image.Image:
    """返回铺满 `size` 的等比裁切图。

    size   目标尺寸（宽, 高）
    zoom   1.0 = 刚好铺满；>1 放大后裁切（构图更紧）
    dx,dy  裁切窗相对居中位置的偏移（正数向右/向下），超界自动夹住
    """
    tw, th = size
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        raise ValueError("empty image")

    scale = max(tw / iw, th / ih) * max(zoom, 1e-6)
    scaled = img.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)

    max_x = max(0, scaled.width - tw)
    max_y = max(0, scaled.height - th)
    left = min(max(0, (scaled.width - tw) // 2 + int(dx)), max_x)
    top = min(max(0, (scaled.height - th) // 2 + int(dy)), max_y)
    return scaled.crop((left, top, left + tw, top + th))
