"""Ask the local Qwen-Image model to light the current sprite as a 3D model.

    python scripts/gen_render3d.py --seeds 301 302 303

The hand-laid 48x48 sprite has a flat, evenly lit look: every face is one tone, so the
box reads as a diagram. This script feeds that sprite back to the model (blown up 16x, so
it is read as one object) and asks for a **studio-lit 3D render** of the same machine,
same parts, same colours. The point is not to ship the render: it is to pick up where the
light actually lands - which face is lit, how deep the recesses go dark, where the contact
shadows sit - and then hand that back into the pixel sprite.

走 `route="edit"`：画布由参考图（16 倍放大的现有贴图）决定，采样起点是
`TextEncodeQwenImage21` 的参考图尺寸 latent。提示词增强器默认开。

产物只作参考光位，不进发布物。
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
    "把参考图 1 里的这台机器当成一个实体的三维模型，按摄影棚布光渲染出来。"
    "结构和部件位置完全不要改：顶部一个装料舱口、里面并排三支滤芯；正面左上是弹匣槽、"
    "中间一块主屏、右侧一块小屏、下方一道横向出料口、右下三个指示灯、底部一格散热百叶。"
    "布光：主光从右前上方 45 度打下来，冷白色，投影边缘柔和；左后侧一盏很弱的冷色补光；"
    "机身上缘一圈极弱的轮廓光。渲染要能看出：顶面是全场最亮的面、顶面前缘有一道窄的暗部；"
    "装料舱口内部越深越暗、舱口四周的顶面上有一圈环境光遮蔽；"
    "机身右面比左面亮；主屏和出料口这种凹进去的槽，上沿一条亮边、下沿一条暗边，"
    "槽里靠近四角的地方发暗；机体与地面接触的地方有一圈很窄的接触阴影。"
    "材质是磨砂工程塑料加一点拉丝金属，不要镜面反射、不要高光斑。"
    "输出单台机器居中、浅灰背景、正面平视略俯视，没有文字、没有人、没有场景、没有投影落在地面上。"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", type=int, default=[301, 302, 303])
    ap.add_argument("--steps", type=int, default=28)
    args = ap.parse_args()

    ref = GEN / "self_v112_x16.png"
    if not ref.exists():
        raise SystemExit(f"缺少参考图 {ref}（先用 make_machine_sprite.py 出稿再放大）")
    for seed in args.seeds:
        out = GEN / f"render3d_s{seed}.png"
        if out.exists():
            print("skip", out.name)
            continue
        print("generating", seed, flush=True)
        res = qwen_gen.generate(
            PROMPT,
            out=out,
            route="edit",
            resolution=1024,
            steps=args.steps,
            seed=seed,
            refs=[ref],
            manifest=GEN / "manifest.json",
            note="打光参考图（只为取光位，不进发布物）",
        )
        print(res.get("ok"), out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
