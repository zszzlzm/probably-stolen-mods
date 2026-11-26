"""用游戏原版素材当参考图，生成「拾荒手记」创意工坊封面关键图（文档档位 1536×1024，之后由 make_cover.py 裁成 1280×720）。

用法：
    python scripts/gen_covers.py a 111
    python scripts/gen_covers.py b 222
"""
import pathlib
import sys

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / "refs"
GEN = ROOT / "art" / "gen"
sys.path.insert(0, str(ROOT.parent / "tools"))
import qwen_gen  # noqa: E402

NEG = (
    "text, letters, logo, watermark, cartoon, anime, bright daylight, clean neon, "
    "low detail, muddy composition, deformed hands, extra fingers, gore, pixel art, pixelated, "
    "low resolution, flat lighting"
)

BASE = (
    "Cinematic game cover key art for a gritty sci-fi scavenging minigame. "
    "Rain-soaked orbital-station junkyard at night, a lone scavenger in a patched hooded coat "
    "crouching beside a steaming pile of scrap, flashlight beam cutting through dust onto sealed "
    "plastic crates and a dead machine. Faint 6x4 grid of metal compartments in the background wall. "
    "Orange incinerator glow far right, cold teal shadows, wet metal, cables, rain streaks. "
    "Painterly concept art, high contrast, strong silhouette, thumbnail-readable, "
    "dark negative space on the left and lower-left for a title. 16:9, 1280x720. "
    "No text, no letters, no logo, no watermark, no cartoon, no anime, no bright daylight, no gore, no deformed hands."
)

# 两种构图：A 是标准三分法，B 换成低机位、人物更靠左下、光柱打在箱子上的近景
SHOTS = {
    "a": BASE,
    "b": (
        "Cinematic game cover key art, low camera angle. Rain-soaked orbital-station junkyard at night. "
        "A lone scavenger in a patched hooded coat crouches in the near foreground at the lower left, "
        "back to camera, silhouetted against the fog; his flashlight beam rakes across a stack of sealed "
        "plastic crates and the ribs of a dead machine half-buried in scrap. A towering heap of rusted "
        "hulls and cables steams in the middle ground, faint 6x4 grid of metal compartments behind. "
        "An incinerator burns orange in the far background, cold teal rain and mist, wet reflective metal, "
        "volumetric light through rain. Painterly concept art, high contrast, strong silhouette, "
        "thumbnail-readable, large dark negative space along the left edge for a title. 16:9, 1280x720. "
        "No text, no letters, no logo, no watermark, no cartoon, no anime, no bright daylight, no gore, no deformed hands."
    ),
}


def upscale(src: pathlib.Path, width: int, dst: pathlib.Path) -> pathlib.Path:
    img = Image.open(src).convert("RGBA")
    h = round(img.height * width / img.width)
    img.resize((width, h), Image.LANCZOS).save(dst)
    return dst


def main():
    shot = sys.argv[1] if len(sys.argv) > 1 else "a"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    GEN.mkdir(parents=True, exist_ok=True)

    game = REFS / "game"
    refs = [
        upscale(game / "debris_pile2.png", 512, GEN / "ref_debris2.png"),
        upscale(game / "debris_pile3.png", 512, GEN / "ref_debris3.png"),
    ]
    out = GEN / f"cover_{shot}.png"
    res = qwen_gen.generate(
        SHOTS[shot],
        negative=NEG,
        out=out,
        size=qwen_gen.COVER,
        route="style",            # 原版废料堆贴图只当风格提示，画布仍是 1536×1024
        steps=qwen_gen.STEPS,
        seed=seed,
        refs=refs,
        manifest=GEN / "manifest.json",
        note="工坊封面关键图；裁切由 make_cover.py 做",
    )
    print({k: res.get(k) for k in ("ok", "seconds", "error", "size", "path")})


if __name__ == "__main__":
    main()
