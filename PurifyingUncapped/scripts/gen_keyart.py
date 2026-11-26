"""生成创意工坊封面用的关键图（文档档位 1536×1024，之后由 make_cover.py 裁成 1280×720）。

走 `route="edit"`：参考图是本仓库里 Pharmacy 的那张封面关键图，画布因此正好 1536×1024；
要求保留它的像素画风、横向构图、右侧光源与左侧虚空，只把内容换成水培种植室。
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = REFS / "gen"

sys.path.insert(0, str(ROOT.parent / "tools"))
import qwen_edit  # noqa: E402
import qwen_gen  # noqa: E402

STYLE_REF = ROOT.parent / "Pharmacy" / "refs" / "gen" / "keyart.png"

PROMPT = (
    "把这张参考图改造成赛博朋克下层区的一间水培种植室，保持原来的 16 位机像素画风格、"
    "横向宽幅构图、右侧的光源方向、整体深色调与青加琥珀的配色，左侧三分之一的安静暗部要保留下来。"
    "把画面右侧那一组物件换成并排的玻璃水培水箱和粗旧的金属管道，"
    "箱里的水清澈泛着青色微光，水面下悬着发光的植物根系，几株改造过的作物在冷光里生长；"
    "再放一台老旧的净水机和一排仪表，背景是昏暗的金属墙壁与冷色霓虹灯管，空气里有漂浮的灰尘和光柱。"
    "画面中没有文字、没有人、没有水印。"
)


def main():
    GEN.mkdir(parents=True, exist_ok=True)
    if not STYLE_REF.exists():
        raise SystemExit(f"缺少参考图 {STYLE_REF}（先跑 Pharmacy/scripts/gen_keyart.py）")
    out = GEN / "keyart.png"
    res = qwen_gen.generate(
        PROMPT,
        out=out,
        route="edit",             # 换场景保留 Pharmacy 封面的构图与色调：画布由参考图定
        # resolution 是「面积≈resolution²」，要正好 1536×1024 得填 1248（见 qwen_edit.resolution_for）
        resolution=qwen_edit.resolution_for(*qwen_gen.COVER),
        steps=qwen_gen.STEPS,
        seed=int(sys.argv[1]) if len(sys.argv) > 1 else 7,
        refs=[STYLE_REF],
        manifest=GEN / "manifest.json",
        note="工坊封面关键图；裁切由 make_cover.py 做",
    )
    print({k: res.get(k) for k in ("ok", "seconds", "error", "size", "path")})


if __name__ == "__main__":
    main()
