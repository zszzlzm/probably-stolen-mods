#!/usr/bin/env python3
"""生成《慷慨买家》封面的关键图候选（文档档位 1536×1024，暗调、无文字）。

参数走 `tools/qwen_gen.py`：steps 25 / 生图前卸载 27B / 每张落 manifest。
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "refs" / "gen"

sys.path.insert(0, str(HERE.parent.parent / "tools"))
import qwen_gen  # noqa: E402

PROMPT = (
    "赛博朋克下层区商店的深夜柜台特写，深色金属台面上一排三只一模一样的白色小药盒整齐排开，"
    "右侧一只穿深色大衣袖口的手把几枚微微发光的信用芯片推过柜台，暖琥珀色侧逆光勾出盒子边缘，"
    "背景是虚化的店铺灯光与货架，浅景深，电影感，暗调，画面左侧留出大片干净的暗部，"
    "写实材质，胶片颗粒，不出现任何文字、标签、logo"
)

SEEDS = [101, 202, 303, 404]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for i, seed in enumerate(SEEDS):
        path = OUT / ("keyart_%s.png" % "abcd"[i])
        print("generating", path.name, "seed", seed, flush=True)
        qwen_gen.generate(
            PROMPT,
            out=path,
            size=qwen_gen.COVER,
            steps=qwen_gen.STEPS,
            seed=seed,
            manifest=OUT / "manifest.json",
            note="封面候选；裁切由 make_cover.py 做",
        )
    print("done")


if __name__ == "__main__":
    main()
