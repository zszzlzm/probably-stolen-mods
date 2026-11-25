"""Turn a generated 1024x1024 machine concept into the game's 48x48 sprite.

    python scripts/pixify_machine.py refs/gen/machine_s22.png --seed-out

Steps
1. cut the concept out of its plain background (flood fill from the corners, which also
   removes the drop shadow);
2. crop to the machine, resize to 44x44 inside a 48x48 canvas so the same 2 px black
   margin the vanilla machine sprites carry is preserved (3x3 grid cells at 16 px);
3. snap every pixel to the vanilla machine palette (``items_tool2``), so values and hue
   match the rest of the game instead of the model's saturated teal / pure red LEDs;
4. tidy the pixel art: kill isolated single pixels, then re-assert the 1 px navy border
   between the machine and the black margin, exactly like the vanilla sprites.
"""

import argparse
import pathlib
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

W = H = 48
MARGIN = 2  # vanilla machine sprites keep a 2 px pure-black margin

# Vanilla machine palette, sampled from Items/items_tool2 and the neon-free part of
# items_amenities. Chinese comments kept short so the table stays readable.
PALETTE = [
    ("E", (0x00, 0x00, 0x00)),  # margin
    ("K", (0x29, 0x22, 0x34)),  # navy outline / recess
    ("M", (0x27, 0x34, 0x56)),  # dark navy backing
    ("m", (0x44, 0x46, 0x4C)),  # seam
    ("B", (0x5F, 0x68, 0x68)),  # body
    ("D", (0x3F, 0x4A, 0x52)),  # body shadow
    ("d", (0x36, 0x3F, 0x4A)),  # deep shade
    ("L", (0x88, 0x94, 0x8A)),  # light bevel
    ("w", (0xA8, 0xAE, 0xA5)),  # light grey
    ("C", (0xD5, 0xD2, 0xB8)),  # cream
    ("c", (0xB9, 0xB4, 0x9A)),  # cream shadow
    ("G", (0x4B, 0x5B, 0x5D)),  # glass
    ("S", (0x80, 0x92, 0x9B)),  # glass sheen
    ("T", (0x27, 0x56, 0x54)),  # teal shadow
    ("t", (0x45, 0x91, 0x8B)),  # teal lit
    ("u", (0x6F, 0xB7, 0xA8)),  # teal highlight
    ("g", (0x3D, 0x82, 0x3F)),  # LED green
    ("a", (0x9F, 0x52, 0x6D)),  # LED mauve
    ("y", (0xD5, 0xA5, 0x4A)),  # LED amber
]

LABELS = [k for k, _ in PALETTE]
RGB = np.array([c for _, c in PALETTE], dtype=np.float32)
# Human perception is more sensitive to green; weight the distance a little.
WEIGHT = np.array([2.0, 4.0, 3.0], dtype=np.float32)

SENTINEL = (1, 2, 3)


def cut_out(img: Image.Image, tol: int = 42) -> Image.Image:
    """Flood the plain background away from all four corners; keep the machine."""
    rgb = img.convert("RGB")
    work = rgb.copy()
    w, h = work.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        try:
            ImageDraw.floodfill(work, seed, SENTINEL, thresh=tol)
        except Exception:
            pass
    arr = np.asarray(work)
    bg = (arr[:, :, 0] == SENTINEL[0]) & (arr[:, :, 1] == SENTINEL[1]) & (arr[:, :, 2] == SENTINEL[2])
    out = np.asarray(img.convert("RGBA")).copy()
    out[bg, 3] = 0
    return Image.fromarray(out, "RGBA")


def resize_premultiplied(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    arr = np.asarray(img).astype(np.float32) / 255.0
    a = arr[:, :, 3]
    rgb = arr[:, :, :3] * a[:, :, None]
    chans = [np.asarray(Image.fromarray(rgb[:, :, i], "F").resize(size, Image.LANCZOS)) for i in range(3)]
    alpha = np.asarray(Image.fromarray(a, "F").resize(size, Image.LANCZOS))
    safe = np.maximum(alpha, 1e-4)[:, :, None]
    out = np.zeros((size[1], size[0], 4), np.float32)
    out[:, :, :3] = np.clip(np.dstack(chans) / safe, 0, 1)
    out[:, :, 3] = np.clip(alpha, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def snap(labels: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    """Nearest palette entry for every cell (alpha already flattened out)."""
    flat = rgb.reshape(-1, 3)
    d = ((flat[:, None, :] - RGB[None, :, :]) * WEIGHT) ** 2
    idx = d.sum(axis=2).argmin(axis=1)
    return idx.reshape(labels.shape)


def despeckle(idx: np.ndarray, rounds: int = 2) -> np.ndarray:
    """Replace lone pixels (all 4 neighbours agree on something else) by the majority."""
    h, w = idx.shape
    out = idx.copy()
    for _ in range(rounds):
        src = out.copy()
        for y in range(h):
            for x in range(w):
                neigh = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        neigh.append(src[ny, nx])
                if len(neigh) == 4 and all(n != src[y, x] for n in neigh):
                    common = Counter(neigh).most_common(1)[0]
                    if common[1] >= 3:
                        out[y, x] = common[0]
    return out


def border_pass(idx: np.ndarray) -> np.ndarray:
    """Give the machine a 1 px navy border like every vanilla machine sprite.

    The concept art has rounded corners and a soft edge; on a 16 px grid that reads as
    a blur. We snap the outermost machine pixels to navy and flatten any stair-step
    narrower than 2 px.
    """
    h, w = idx.shape
    machine = idx != LABELS.index("E")
    navy = LABELS.index("K")
    out = idx.copy()
    for y in range(h):
        for x in range(w):
            if not machine[y, x]:
                continue
            edge = any(
                not (0 <= x + dx < w and 0 <= y + dy < h) or not machine[y + dy, x + dx]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if edge:
                out[y, x] = navy
    return out


def build_sprite(concept: Image.Image, inset: int = 4) -> tuple[Image.Image, np.ndarray]:
    """Concept -> 48x48 sprite with a forced, crisp machine frame.

    The model draws rounded corners and soft edges; on a 16 px grid that turns into
    mush, so the silhouette is *not* taken from the model. Every vanilla machine is a
    full square canvas with a 2 px black margin and a 1 px navy border, and the body
    starts at pixel 3-4. We keep the model's interior (magazine / screen / slot / LEDs)
    and re-assert that frame around it.
    """
    cut = cut_out(concept)
    bbox = cut.getchannel("A").getbbox()
    if bbox is None:
        raise SystemExit("nothing left after cutting the background")
    cut = cut.crop(bbox)

    inner = W - inset * 2
    small = resize_premultiplied(cut, (inner, inner))

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    canvas.alpha_composite(small, (inset, inset))

    arr = np.asarray(canvas).astype(np.float32)
    idx = despeckle(snap(np.zeros((H, W), np.int32), arr[:, :, :3]), rounds=2)

    k = LABELS.index("K")
    e = LABELS.index("E")
    # outside the machine: pure black margin, exactly like the vanilla sprites
    idx[:MARGIN, :] = e
    idx[H - MARGIN:, :] = e
    idx[:, :MARGIN] = e
    idx[:, W - MARGIN:] = e
    # 1 px navy border, light bevel top/left, shadow bottom/right
    idx[MARGIN, MARGIN:W - MARGIN] = k
    idx[H - MARGIN - 1, MARGIN:W - MARGIN] = k
    idx[MARGIN:H - MARGIN, MARGIN] = k
    idx[MARGIN:H - MARGIN, W - MARGIN - 1] = k
    light = LABELS.index("L")
    shadow = LABELS.index("D")
    idx[MARGIN + 1, MARGIN + 1:W - MARGIN - 1] = light
    idx[MARGIN + 1:H - MARGIN - 1, MARGIN + 1] = light
    idx[H - MARGIN - 2, MARGIN + 1:W - MARGIN - 1] = shadow
    idx[MARGIN + 1:H - MARGIN - 1, W - MARGIN - 2] = shadow

    out = Image.new("RGBA", (W, H))
    px = out.load()
    for y in range(H):
        for x in range(W):
            r, g, b = PALETTE[idx[y, x]][1]
            px[x, y] = (r, g, b, 255)
    return out, idx


def preview(sprite: Image.Image, scale: int = 8, bg=(38, 38, 44, 255)) -> Image.Image:
    img = Image.new("RGBA", (sprite.width * scale, sprite.height * scale), bg)
    img.alpha_composite(sprite.resize((sprite.width * scale, sprite.height * scale), Image.NEAREST))
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("concept")
    ap.add_argument("--out", default="")
    ap.add_argument("--preview", default="")
    args = ap.parse_args()

    src = pathlib.Path(args.concept)
    sprite, _ = build_sprite(Image.open(src))

    out = pathlib.Path(args.out) if args.out else src.with_name(src.stem + "_48.png")
    sprite.save(out)
    pv = pathlib.Path(args.preview) if args.preview else src.with_name(src.stem + "_48_preview.png")
    preview(sprite).save(pv)
    print("sprite ", out, sprite.size, out.stat().st_size, "bytes")
    print("preview", pv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
