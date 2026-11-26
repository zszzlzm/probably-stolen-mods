"""Ask the local Qwen-Image model for a machine body whose TOP FACE is visible.

    python scripts/gen_3d_edit.py --seeds 201 202 203

The vanilla machines are drawn from slightly above (their top surface is a band that
narrows towards the back), while the 1.1.x sprite was a plain front elevation. This
script asks the model to re-see our own 48x48 draft from above: the reference images are
the current draft blown up 10x, plus vanilla ``printer_off`` and ``furnace`` blown up 16x
so the model keeps the game's own modelling language.

走 `route="edit"`：画布由第一张参考图（放大 10 倍的现有贴图）决定，
采样起点是 `TextEncodeQwenImage21` 的参考图尺寸 latent，不是自己新建的空 latent
（文档 §13 细节 1，`nodes_qwen.py:138-140`）。提示词增强器默认开，
用 `QWEN_ENHANCE=0` 可以只跑原始提示词做对比。

产物只用来定形：48 px 的贴图仍然手排（`make_machine_sprite.py`）。
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
    "把参考图 1 这台滤芯打印机改画成俯视正面的视角：机身顶部要露出一整块朝上的平面，"
    "这块平面靠后的一侧窄、靠前的一侧宽，是一块梯形；平面上前一半是向内凹进去的装料井，"
    "井里并排立着三支米白色滤芯，只看得到滤芯的顶盖和一小截筒身，"
    "井的前沿有一条亮边横切过去、压住三支滤芯的下沿；平面上后一半留成平整的顶盖，"
    "顶盖和井之间有一道很细的接缝。"
    "机身正面的部件位置保持不变：左侧竖排滤芯弹匣、右侧方形小屏、中间主屏、"
    "下方横向出料口里躺着一支露一半的滤芯、右下角三个指示灯。"
    "画法像参考图 2、3 里原版游戏的机器：一像素粗的深蓝近黑描边，颜色不超过 10 种，"
    "每块像素约 20 像素见方，顶面比正面亮一档，没有渐变、没有高光渐变、"
    "没有文字、没有人、没有地面、没有背景。"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[201, 202, 203])
    ap.add_argument("--steps", type=int, default=28)
    args = ap.parse_args()

    refs = [
        pathlib.Path(p)
        for p in (
            GEN / "self_c_x10.png",        # 当前手排稿（候选 C）放大 10 倍
            GEN / "ref_printer_x16.png",   # 原版 3D 打印机
            GEN / "ref_furnace_x16.png",   # 原版熔炉：梯形顶面最清楚
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
            note="顶面定形概念图（增强器改写指令 → 编辑图）",
        )
        print(res.get("ok"), out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
