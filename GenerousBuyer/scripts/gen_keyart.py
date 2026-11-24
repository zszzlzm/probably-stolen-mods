#!/usr/bin/env python3
"""生成《慷慨买家》封面的关键图候选（1280x720，暗调、无文字）。"""
import pathlib
import subprocess
import sys

TOOL = r"F:\随笔集\完全自由的异世界之旅\04_工具\qwen_img.py"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "refs" / "gen"

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
        cmd = [
            sys.executable, TOOL, PROMPT,
            "-o", str(path),
            "--width", "1280", "--height", "720",
            "--steps", "30", "--seed", str(seed),
        ]
        print("generating", path.name, "seed", seed, flush=True)
        subprocess.run(cmd, check=True)
    print("done")


if __name__ == "__main__":
    main()
