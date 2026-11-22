"""把图标颜色吸附到游戏自己的调色板上。

调色板直接从 refs/tex_items_medical.png（游戏原版医疗物品图集）统计出来，
所以生成的图标只会用原版美术里真实存在的颜色。
"""
import numpy as np
from PIL import Image


def build_palette(ref_png="refs/tex_items_medical.png", colors=32):
    img = Image.open(ref_png).convert("RGBA")
    a = np.asarray(img)
    opaque = a[:, :, 3] > 200
    rgb = a[:, :, :3][opaque]
    if len(rgb) == 0:
        raise SystemExit("reference has no opaque pixels")
    # 用中位切分统计主色，再去重
    flat = Image.fromarray(rgb.reshape(1, -1, 3), "RGB")
    q = flat.quantize(colors=colors, method=Image.MEDIANCUT).convert("RGB")
    pal = np.asarray(q).reshape(-1, 3)
    uniq = []
    for c in pal:
        if not any(np.abs(c - u).sum() <= 6 for u in uniq):
            uniq.append(c)
    return np.array(uniq, dtype=np.int32)


def snap(img, palette, alpha_cut=8):
    arr = np.asarray(img.convert("RGBA")).astype(np.int32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    mask = alpha > alpha_cut
    if mask.any():
        px = rgb[mask]  # N x 3
        d = ((px[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)
        nearest = palette[d.argmin(axis=1)]
        rgb[mask] = nearest
    out = np.dstack([rgb.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pixify as px

    pal = build_palette()
    print("palette colors:", len(pal))
    oc = tuple(int(v) for v in pal[np.argsort(pal.sum(axis=1))[0]])
    print("darkest (outline):", oc)
    for key in sys.argv[1:]:
        s = Image.open(f"refs/gen/{key}_16.png")
        m = snap(s, pal)
        m = px.add_outline(m, color=oc)
        m.save(f"refs/gen/{key}_16_palette.png")
        px.preview(m).save(f"refs/gen/{key}_16_palette_preview.png")
        print("palette-matched", key)
