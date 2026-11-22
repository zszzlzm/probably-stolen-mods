"""生成滤芯打印机封面用的关键图（1280x720）。参考图来自游戏原版滤水/滤芯素材。"""
import os
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = REFS / "gen"
# 游戏素材目录（默认指向本仓库同级的 ScavGame/refs/game，可用 PS_GAME_REFS 覆盖）
GAME = pathlib.Path(os.environ.get("PS_GAME_REFS", ROOT.parent / "ScavGame" / "refs" / "game"))

# 生图入口 qwen_img.py 所在目录，用 QWEN_IMG_DIR 指定
QWEN_DIR = os.environ.get("QWEN_IMG_DIR", r"F:\随笔集\完全自由的异世界之旅\04_工具")
sys.path.insert(0, QWEN_DIR)
import qwen_img  # noqa: E402

PROMPT = (
    "像素艺术风格的游戏场景插画，16 位机像素画，赛博朋克下层区的一间小型印刷工坊工作台。"
    "深色金属台面上放着一台改装过的滤芯打印机：方形工业外壳、几根粗电缆、发光的青色出料口，"
    "正从打印床上送出一枚刚成型的圆柱形滤芯，滤芯内部透出淡青色的滤网纹理；"
    "旁边排着几枚贴着彩色标签的旧滤芯、金属线轴和散落的工具，"
    "背景是昏暗的货架与冷色霓虹灯牌，空气里有蒸汽和光柱。"
    "整体深色调，青色和琥珀色点缀，横向宽幅构图，光源在右侧，"
    "画面左边三分之一留出大片安静暗部用于排版文字，画面中没有文字、没有人、没有水印。"
)


def upscale(src, factor, dst):
    img = Image.open(src).convert("RGBA")
    img.resize((img.width * factor, img.height * factor), Image.NEAREST).save(dst)
    return dst


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    refs = [
        upscale(GAME / "purifier.png", 8, GEN / "ref_purifier_x8.png"),
        upscale(GAME / "water_filter.png", 16, GEN / "ref_filter_x16.png"),
        upscale(GAME / "water_filter_adv.png", 12, GEN / "ref_filter_adv_x12.png"),
    ]
    out = GEN / "keyart.png"
    res = qwen_img.generate(
        PROMPT,
        out=out,
        width=1280,
        height=720,
        steps=30,
        seed=int(sys.argv[1]) if len(sys.argv) > 1 else 7,
        refs=refs,
        unload_27b=False,
    )
    print({k: res.get(k) for k in ("ok", "seconds", "error", "size", "path")})


if __name__ == "__main__":
    main()
