"""Generate sprite candidates with the local Qwen-Image model.

  python scripts/gen_assets.py <asset> <seed> [--out DIR]

Each asset is generated at an exact multiple of its logical pixel grid (32x per
logical pixel, capped at 1024 px), so a nearest-neighbour downscale reproduces
the intended 16x32 / 32x32 / 48x64 sprite.
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE.parent / "refs" / "model"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import qwen_gen  # noqa: E402

STYLE = (
    "Pixel-art game item sprite for a 2D space-station farming game. "
    "The whole image is exactly {gw} by {gh} logical pixels, upscaled {scale}x: one logical pixel = one flat {scale}px square, "
    "hard blocky edges, absolutely no anti-aliasing, no blur, no gradient, no glow, no soft shading, no texture. "
    "Muted limited palette: dark plum outline #292234, deep brown #7d4f4a, muted brown #a4715d, cream #c5ac96, "
    "dark teal #275654, teal #2f756f, brighter teal #45918b, pale teal #8abfbb, leaf green #3d823f. "
    "One single centered game item filling most of the frame, flat colors, dark plum outlines, no pedestal, "
    "no ground shadow, no frame, no border, no text, perfectly flat solid magenta #ff00ff background."
)

FLAT_STYLE = (
    "Game item icon for a 2D space-station farming game, flat cel-shaded style, thick dark plum outline #292234, "
    "three flat colors per material, hard edges, no gradient, no texture, no glow, no anti-aliasing, "
    "muted palette: green #3d823f, dark green #41603f, dark teal #275654, teal #2f756f, pale teal #8abfbb, "
    "cream #c5ac96, muted brown #a4715d. Single centered item filling most of the frame, no pedestal, "
    "no ground shadow, no frame, no text, perfectly flat solid magenta #ff00ff background."
)

ASSETS = {
    "fern_web": {
        "grid": (16, 32),
        "refs": ["../../refs/web/web_02.jpg", "hydroreed_filter_ref.png"],
        "prompt": (
            "Copy the silhouette and leaflet rhythm of the fern photo in the first reference image: "
            "one upright frond with paired saw-toothed leaflets, tapering to a point at the top. "
            "Recolor it with the muted teal-green palette of the second reference (the game sprite), "
            "keep the thick leaf shapes, simplify to a few big leaflets so it reads at 16x32 pixels."
        ),
    },
    "fern_flat": {
        "grid": (16, 32),
        "refs": ["hydroreed_filter_ref.png"],
        "prompt": (
            "Flat game icon of a fern bundle, NOT pixel art: two upright fronds side by side, "
            "each with a pale teal stem and simple paired grey-green leaflets, thick dark plum outline around "
            "the whole silhouette, three flat green tones, cell-shaded with hard edges, no gradients, no texture, "
            "single centered icon filling the frame, solid flat magenta #ff00ff background."
        ),
    },
    "fern": {
        "grid": (16, 32),
        "refs": ["../../refs/web/web_02.jpg", "hydroreed_filter_ref.png"],
        "prompt": (
            "A very simplified pixel-art fern bundle designed to read at 16x32 pixels: three thick upright stems "
            "standing side by side, the middle one tallest (nearly the full height) and the two outer ones shorter "
            "and leaning slightly outward, like the fern photo in the first reference. Each stem carries four to six "
            "pairs of chunky angled leaflets, every leaflet a solid two-pixel-wide block, plus a flat pale-teal vein "
            "stripe running up the middle stem. The bundle fills the tall frame from edge to edge: the middle "
            "frond's tip reaches close to the top, the stems reach the bottom, and the whole bundle stays narrow. "
            "The three fronds are clearly separated - leave a thin empty gap of "
            "background between them all the way down, they only meet at the bottom in a small bundle. "
            "The leaflets are GREEN like the second reference's plant - leaf green "
            "#3d823f on top and dark green #41603f in shadow - NOT brown, NOT beige. Big readable shapes only, thick "
            "forms, nothing thin, one-pixel dark plum outline around the whole silhouette."
        ),
    },
    "fern_s": {
        "grid": (16, 16),
        "refs": ["dream_cap_s_ref.png"],
        "prompt": (
            "A tiny fern fiddlehead drawn as one simple thick spiral, like a rolled-up frond: "
            "a two-pixel-thick pale teal line curling inward one and a half turns, leaving a clear empty hole "
            "in the middle, with a short stem dropping to the bottom edge. Only two teal tones plus a dark outline, "
            "no speckles, no extra leaves, no shading bands, nothing else in frame."
        ),
    },
    "fern_l": {
        "grid": (32, 32),
        "refs": ["dream_cap_l_ref.png", "hydroreed_filter_ref.png"],
        "prompt": (
            "A generous fan of five fern fronds spreading upward and outward, filling the 32x32 frame. "
            "Pale grey-green leaflets, dark teal shadows between fronds, flat pale-teal vein stripes up the "
            "front stems, several muted green tones, clearly a big lush bundle."
        ),
    },
    "seed": {
        "grid": (16, 16),
        "refs": ["dream_cap_seed_ref.png", "hydroreed_seed_ref.png"],
        "prompt": (
            "A chunky square spore jar for the fern, designed to read at 16x16: a glass jar with a flat metal "
            "screw cap, a big cream label filling the middle of the jar, and a single dark teal fern leaf icon "
            "printed on the label instead of any text, pale teal glass at the shoulders, thick dark plum outline."
        ),
    },
    "plant_p": {
        "grid": (48, 64),
        "refs": ["hydroreed_p_ref.png", "restoring_fern_l_ref.png"],
        "prompt": (
            "A young fern clump for a hydroponic tray, drawn as a pixel-art game sprite with BIG SIMPLE SHAPES, "
            "leaves are chunky 3-4 pixel blocks, not fine filigree, only five thick fronds, "
            "shaped like a LOW WIDE bush - about 46 pixels wide by 36 tall, much wider than tall, "
            "fronds spreading sideways more than upwards, the whole plant dense and compact: "
            "seven thin fronds fanning up and out from one narrow base, every frond curved "
            "like an arc rather than a straight stick, and each frond carrying many small "
            "leaflets that point up and outward at an angle - never flat horizontal bars. "
            "The leaflets are leaf green #3d823f with dark green #41603f undersides, the "
            "stems are muted teal #2f756f, and a few tips catch pale teal light #8abfbb. "
            "Below the clump, four short teal roots dangle in different lengths. "
            "No tray, no pot, no water surface, no ground shadow, no text. "
            "Dense and slightly irregular like the reeds in the first reference, "
            "same thickness of outline as the sprite in the second reference, "
            "perfectly flat solid magenta #ff00ff background."
        ),
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset", choices=sorted(ASSETS))
    ap.add_argument("seed", type=int)
    ap.add_argument("--out", default=str(HERE.parent / "refs" / "gen"))
    ap.add_argument("--steps", type=int, default=30)
    args = ap.parse_args()

    spec = ASSETS[args.asset]
    gw, gh = spec["grid"]
    flat = args.asset.endswith("_flat")
    # 文档档位：长边至少 1024 px（模型在 512 以下细节会塌），仍保持整数倍最近邻缩放
    scale = max(32, (1024 + max(gw, gh) - 1) // max(gw, gh))
    width, height = gw * scale, gh * scale
    if flat:
        prompt = FLAT_STYLE + " " + spec["prompt"]
    else:
        prompt = STYLE.format(gw=gw, gh=gh, scale=scale) + " " + spec["prompt"]
    refs = [REF / r for r in spec["refs"]]
    for r in refs:
        if not r.exists():
            raise SystemExit(f"missing ref {r}")

    out = pathlib.Path(args.out) / f"{args.asset}_s{args.seed}.png"
    res = qwen_gen.generate(
        prompt,
        out=out,
        size=(width, height),
        negative=(
            "blurry, 3d render, realistic photo, smooth gradient, airbrush, glow, bloom, neon, halo, "
            "perspective, multiple scattered objects, scenery, text, watermark, frame, border, "
            "anti-aliasing, noise, film grain, tiny details"
        ),
        steps=args.steps,
        seed=args.seed,
        refs=refs,
        manifest=pathlib.Path(args.out) / "manifest.json",
        note=f"{gw}x{gh} logical px, upscale {scale}x",
    )
    print(res)


if __name__ == "__main__":
    main()
