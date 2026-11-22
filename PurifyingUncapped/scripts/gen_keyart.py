"""生成创意工坊封面用的关键图（1280x720）。风格参考 Pharmacy 的封面关键图（同一套下层区色调）。"""
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = REFS / "gen"

sys.path.insert(0, r"F:\随笔集\完全自由的异世界之旅\04_工具")
import qwen_img  # noqa: E402

STYLE_REF = pathlib.Path(r"F:\随笔集\完全自由的异世界之旅") / "deepseek-harness/default-workspace/Pharmacy/refs/gen/keyart.png"

PROMPT = (
    "像素艺术风格的游戏场景插画，16 位机像素画，赛博朋克下层区的一间水培种植室。"
    "画面右侧是一组玻璃水培水箱和粗旧的金属管道，箱里的水清澈泛着青色微光，"
    "水面下悬着发光的植物根系，几株改造过的作物在冷光里生长；旁边有一台老旧的净水机和一排仪表，"
    "背景是昏暗的金属墙壁与冷色霓虹灯管，空气里有漂浮的灰尘和光柱。"
    "整体深色调，青色和一点点琥珀色点缀，横向宽幅构图，光源在右侧，"
    "画面左边三分之一留出大片安静暗部用于排版文字，画面中没有文字、没有人、没有水印。"
)


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    refs = [STYLE_REF] if STYLE_REF.exists() else []
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
