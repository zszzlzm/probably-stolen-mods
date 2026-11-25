"""Generate candidate art for the filter cartridge printer with the local Qwen-Image model.

    python scripts/gen_machine_art.py --seeds 11 22 33 44

The model is only used for the *idea* (silhouette, where the rack / screen / output
slot sit, how the light falls). The result is downscaled onto the game's 16 px grid
afterwards by ``scripts/pixify_machine.py``, which snaps colours to the vanilla
machine palette and re-draws the outline - so nothing in the final sprite depends on
the model getting individual pixels right.
"""

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
GEN = HERE / "refs" / "gen"
GEN.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, r"F:\随笔集\完全自由的异世界之旅\04_工具")
import qwen_img  # noqa: E402

STYLE = (
    "像素艺术游戏道具贴图，复古 16 位像素风，单台机器，正面平视，机器居中占满画面，"
    "外壳为接近正方形的大方块，四个角都是直角，机器底部与画布底部对齐，"
    "深色描边粗 1 像素块，颜色只有 6 到 7 种，"
    "像素块大而整齐、每块约 20 像素宽、边缘笔直、没有抗锯齿、没有渐变、没有高光反光，"
    "没有文字、没有人物、没有地面、没有投影，背景是纯深灰留白。"
)

PROMPT = STYLE + (
    "这台机器是「滤芯打印机」：米白色机身，青绿色装饰条横在顶部，"
    "机身左侧三分之一是一道竖向的透明弹匣，弹匣里并排竖着三支白色圆柱形滤芯，"
    "正面右侧三分之一是一块深色方形小屏幕，屏幕上有一个青绿色的漏斗图标，"
    "正面下半部是一道横向出料口，一支白色滤芯正从出料口里吐出来、只露出一半，"
    "底部右下角有三个彩色小指示灯。"
    "与参考图里的工业机器是同一种美术风格、同一种颜色明暗关系（左上亮、右下暗）。"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[11, 22, 33, 44])
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--refs", nargs="*", default=[])
    args = ap.parse_args()

    refs = [pathlib.Path(p) for p in args.refs]
    for seed in args.seeds:
        out = GEN / f"machine_s{seed}.png"
        if out.exists():
            print("skip existing", out.name)
            continue
        print("generating seed", seed, flush=True)
        res = qwen_img.generate(
            PROMPT,
            out=out,
            negative=qwen_img.NEG_DEFAULT,
            width=args.width,
            height=args.height,
            steps=args.steps,
            seed=seed,
            unload_27b=True,
            refs=refs or None,
            timeout=900,
        )
        print(res.get("ok"), out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
