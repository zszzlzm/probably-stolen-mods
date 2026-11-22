"""生成创意工坊封面用的关键图（1280x720），参考图用游戏自己的素材。"""
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = REFS / "gen"

sys.path.insert(0, r"F:\随笔集\完全自由的异世界之旅\04_工具")
import qwen_img  # noqa: E402

PROMPT = (
    "像素艺术风格的游戏场景插画，16 位机像素画，赛博朋克下层区的一间小药店工作台。"
    "深色金属台面上放着一支装着淡青色药液的小玻璃瓶和一片白色刻痕药片，旁边散落着几只空的小药瓶、"
    "一台旧的化学精制机和一张手写价签，背景是昏暗的货架与冷色霓虹灯牌，空气里有漂浮的灰尘和光柱。"
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
        REFS / "tex_items_medical.png",
        upscale(ROOT / "mod/Textures/Items/calm_agent.png", 16, GEN / "ref_vial_x16.png"),
        upscale(ROOT / "mod/Textures/Items/painkiller_pill.png", 16, GEN / "ref_pill_x16.png"),
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
