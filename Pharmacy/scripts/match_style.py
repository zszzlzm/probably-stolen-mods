"""把生成的图标调成原版图标的色调：饱和度/明度对齐 + 统一描边色。

要点：减色只在物品本身的像素上做（透明区不参与调色板统计），
否则黑底会吃掉调色板名额，白色药片会被量化成奇怪的颜色。
"""
import colorsys

import numpy as np
from PIL import Image


def stats(img):
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    rgb = a[:, :, :3] / 255.0
    alpha = a[:, :, 3] > 8
    if not alpha.any():
        return 0.0, 0.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return float(sat[alpha].mean()), float(mx[alpha].mean())


def outline_color(img):
    a = np.asarray(img.convert("RGBA"))
    alpha = a[:, :, 3] > 200
    rgb = a[:, :, :3]
    lum = rgb.astype(int).sum(axis=2)
    idx = np.argsort(lum[alpha])[: max(4, int(alpha.sum() * 0.06))]
    dark = rgb[alpha][idx]
    return tuple(int(v) for v in dark.mean(axis=0))


def _quantize_opaque(img, colors):
    """只对不透明区域减色，再按原 alpha 贴回去。"""
    arr = np.asarray(img.convert("RGBA")).astype(np.uint8)
    alpha = arr[:, :, 3]
    mask = alpha > 8
    if not mask.any():
        return img
    ys, xs = np.nonzero(mask)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    crop = img.crop(box).convert("RGBA")
    c_arr = np.asarray(crop).astype(np.uint8)
    c_mask = c_arr[:, :, 3] > 8
    # 用物品主色填满透明处，让调色板集中在物品上
    if c_mask.any():
        dominant = np.median(c_arr[:, :, :3][c_mask], axis=0)
    else:
        dominant = np.array([128, 128, 128])
    filled = c_arr[:, :, :3].copy()
    filled[~c_mask] = dominant.astype(np.uint8)
    q = Image.fromarray(filled, "RGB").quantize(colors=colors, method=Image.FASTOCTREE,
                                                dither=Image.NONE).convert("RGB")
    q_arr = np.asarray(q)
    out = np.dstack([q_arr, c_arr[:, :, 3]])
    crop_out = Image.fromarray(out, "RGBA")
    canvas = Image.new("RGBA", img.size, (0, 0, 0, 0))
    canvas.paste(crop_out, (box[0], box[1]), crop_out)
    return canvas


def match_style(src, ref, colors=8, sat_clamp=(0.6, 1.0), val_clamp=(0.85, 1.15)):
    rs, rv = stats(ref)
    ss, sv = stats(src)
    arr = np.asarray(src.convert("RGBA")).astype(np.float32)
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3] / 255.0
    k_s = float(np.clip(rs / max(ss, 1e-3), sat_clamp[0], sat_clamp[1]))
    k_v = float(np.clip(rv / max(sv, 1e-3), val_clamp[0], val_clamp[1]))
    out = rgb.copy()
    for y in range(rgb.shape[0]):
        for x in range(rgb.shape[1]):
            if alpha[y, x] <= 8:
                continue
            h, l, s = colorsys.rgb_to_hls(*rgb[y, x])
            out[y, x] = colorsys.hls_to_rgb(h, min(1.0, l * k_v), min(1.0, s * k_s))
    img = Image.fromarray(np.dstack([(out * 255).astype(np.uint8), alpha.astype(np.uint8)]), "RGBA")
    return _quantize_opaque(img, colors)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pixify as px

    ref = Image.open("refs/dream_dust.png")
    oc = outline_color(ref)
    print("reference sat/val", stats(ref), "outline", oc)
    for key in sys.argv[1:]:
        s = Image.open(f"refs/gen/{key}_16.png")
        m = match_style(s, ref)
        m = px.add_outline(m, color=oc)
        m.save(f"refs/gen/{key}_16_matched.png")
        px.preview(m).save(f"refs/gen/{key}_16_matched_preview.png")
        print("matched", key, stats(m))
