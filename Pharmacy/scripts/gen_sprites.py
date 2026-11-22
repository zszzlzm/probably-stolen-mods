"""用本机 ComfyUI（Qwen-Image 2.1）生成两件药品的物品图标。

参考图取自游戏自己的贴图集（UnityPy 从 sharedassets0.assets 导出）：
  refs/tex_items_medical.png  原版医疗物品图集 512x512
  refs/dream_dust.png         梦尘小瓶 16x16（放大 8 倍后再当参考）
  refs/oxycodone_pill.png     芬太尼药片 16x16（放大 8 倍后再当参考）

用法：
  python scripts/gen_sprites.py calm_agent            # 生成并处理
  python scripts/gen_sprites.py calm_agent --reuse    # 只用已有的 512 原图重做 16x16
"""
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = REFS / "gen"
GEN.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, r"F:\随笔集\完全自由的异世界之旅\04_工具")
sys.path.insert(0, str(HERE))
import qwen_img  # noqa: E402
import pixify as px  # noqa: E402

STYLE = (
    "像素艺术游戏物品图标，16 位机复古像素风，单个物品居中，正面平视，"
    "深色描边，明暗两档上色，边缘干净，周围留出空白，背景完全透明，"
    "画面中只有一个物品，没有文字、没有人、没有地面、没有阴影。"
)

PROMPTS = {
    "calm_agent": (
        STYLE
        + "物品是一支矮胖的小玻璃药瓶，整体接近正方形（宽高比约 1 : 1.15），"
        + "瓶里是淡青色的澄清药液，只有一个白色软木塞，瓶身贴着一圈很窄的白色标签，蓝色调，"
        + "外形轮廓非常粗的深色描边，颜色只有 5 到 6 种，像素块大而清晰，"
        + "与参考图里的药品小瓶是同一种美术风格、同一种大小比例。"
    ),
    "painkiller_pill": (
        STYLE
        + "物品是一片单独的药片，正圆形的白色药片，中间有一道横向刻痕，边缘略微磨损，"
        + "右下方有一小块暖灰色暗面，"
        + "外形轮廓非常粗的深色描边，颜色只有 5 到 6 种，像素块大而清晰，"
        + "与参考图里的药片图标是同一种美术风格、同一种大小比例。"
    ),
}


def _upscale(src, factor, dst):
    img = Image.open(src).convert("RGBA")
    img.resize((img.width * factor, img.height * factor), Image.NEAREST).save(dst)
    return dst


def refs_for(key):
    refs = [REFS / "tex_items_medical.png"]
    if key == "calm_agent":
        refs.append(_upscale(REFS / "dream_dust.png", 8, GEN / "ref_dream_dust_x8.png"))
    else:
        refs.append(_upscale(REFS / "oxycodone_pill.png", 8, GEN / "ref_oxycodone_x8.png"))
    return refs


def generate(key, seed=0, size=512):
    out = GEN / f"{key}_{size}.png"
    res = qwen_img.generate(
        PROMPTS[key],
        out=out,
        width=size,
        height=size,
        steps=25,
        seed=seed,
        refs=refs_for(key),
        unload_27b=False,
    )
    print(key, {k: res.get(k) for k in ("ok", "seconds", "error", "size")})
    return out if res.get("ok") else None


def process(key, path, size=16):
    sprite = px.pixify(Image.open(path), size=size)
    sprite.save(GEN / f"{key}_{size}.png")
    px.preview(sprite).save(GEN / f"{key}_{size}_preview.png")
    print("wrote", GEN / f"{key}_{size}.png")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    reuse = "--reuse" in sys.argv
    for key in args or list(PROMPTS):
        path = GEN / f"{key}_512.png"
        if not (reuse and path.exists()):
            path = generate(key) or path
        if path.exists():
            process(key, path)
