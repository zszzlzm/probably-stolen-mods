"""Ask the local Qwen-Image model to make the hand-drawn sprite look three-dimensional.

    python scripts/gen_3d_edit.py --seeds 101 102 103

Inputs are reference images, not prompts alone: the current 48x48 sprite blown up 10x
(so the model keeps the layout and palette) plus the vanilla printer and chem finisher
blown up 16x (so it keeps the game's modelling language - chamfers, recessed panels,
cast shadows). The point is to *see* alternatives quickly; the pixel sprite itself is
still finished by hand afterwards.

走 `route="edit"`：画布由第一张参考图（放大 10 倍的现有贴图）决定，
采样起点是 `TextEncodeQwenImage21` 的参考图尺寸 latent，不是自己新建的空 latent
（文档 §13 细节 1，`nodes_qwen.py:138-140`）。提示词增强器默认开，
用 `QWEN_ENHANCE=0` 可以只跑原始提示词做对比。
"""

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
GEN = HERE / "refs" / "gen"
GEN.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(HERE.parent / "tools"))
import qwen_gen  # noqa: E402

PROMPT = (
    "像素艺术游戏贴图改造：把参考图 1 里的这台机器重新画成有体积的立体机器，"
    "不要再是平面正面图。要求：能看见机器顶面的厚度和斜面（顶面画成后窄前宽的梯形），"
    "顶面上有一个向内凹进去的装料口，里面插着三支米白色滤芯；"
    "正面的屏幕和出料口都向里凹进一层，凹口的上沿有暗部、下沿有一道亮边；"
    "出料口里躺着一支米白色滤芯，滤芯的下半截被出料口的前沿挡住一点；"
    "机器的底边和凸出的部件下面各有一像素的投影。"
    "保持原来的部件位置（左侧竖排滤芯弹匣、右侧方形屏幕、下方横向出料口、右下角三个指示灯）"
    "和原来的配色（灰绿机身、米白滤芯、青绿饰条、深蓝近黑的描边）。"
    "画法要像参考图 2、3 里原版游戏的机器：一像素粗的深色描边，颜色不超过 8 种，"
    "每块像素约 15 像素见方，没有渐变、没有高光渐变、没有文字、没有人、没有地面、没有背景。"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[101, 102, 103])
    ap.add_argument("--steps", type=int, default=28)
    args = ap.parse_args()

    refs = [
        pathlib.Path(p)
        for p in (
            GEN / "self_sprite_x10.png",
            GEN / "ref_printer_x16.png",
            GEN / "ref_chemfinisher_x16.png",
        )
        if p.exists()
    ]
    for seed in args.seeds:
        out = GEN / f"edit3d_s{seed}.png"
        if out.exists():
            print("skip", out.name)
            continue
        print("generating", seed, flush=True)
        res = qwen_gen.generate(
            PROMPT,
            out=out,
            route="edit",             # 改造现有贴图：画布跟着参考图走
            resolution=1024,
            steps=args.steps,
            seed=seed,
            refs=refs,
            manifest=GEN / "manifest.json",
            note="立体化概念图（增强器改写指令 → 编辑图）",
        )
        print(res.get("ok"), out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
