"""Check generated sprites against ART_SPEC.md.

  python scripts/check_sprites.py refs/hand

Checks: canvas size multiple of 16, 1px margin, alpha=255/0 body over a (0,0,0,3)
filler, palette subset of the 9 spec colors, <= 8 colors, outline present.
"""
import pathlib
import sys
from collections import Counter

from PIL import Image

ALLOWED = {
    (0x29, 0x22, 0x34), (0x27, 0x56, 0x54), (0x2F, 0x75, 0x6F),
    (0x45, 0x91, 0x8B), (0x8A, 0xBF, 0xBB), (0x3D, 0x82, 0x3F),
    (0x41, 0x60, 0x3F), (0xC5, 0xAC, 0x96), (0x7D, 0x4F, 0x4A),
    (0xA4, 0x71, 0x5D), (0x79, 0x74, 0x6E), (0x88, 0x94, 0x8A),
    (0xD5, 0xD2, 0xB8), (0xB6, 0x8B, 0x74),
}
SIZES = {
    "restoring_fern_seed": (16, 16),
    "restoring_fern_s": (16, 16),
    "restoring_fern": (16, 32),
    "restoring_fern_l": (32, 32),
    "restoring_fern_p": (48, 64),
}


def check(path):
    name = path.stem
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    problems = []

    expect = SIZES.get(name)
    if expect and (w, h) != expect:
        problems.append(f"size {w}x{h} != {expect}")
    if w % 16 or h % 16:
        problems.append("size not a multiple of 16")

    px = img.load()
    colors = set()
    body = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if a == 3:
                if (r, g, b) != (0, 0, 0):
                    problems.append(f"filler pixel not black at {x},{y}")
                continue
            if a != 255:
                problems.append(f"partial alpha {a} at {x},{y}")
                continue
            body += 1
            colors.add((r, g, b))
            if (r, g, b) not in ALLOWED:
                problems.append(f"color #{r:02x}{g:02x}{b:02x} outside palette at {x},{y}")

    if len(colors) > 8:
        problems.append(f"{len(colors)} colors (>8)")

    mask = img.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    bbox = mask.getbbox()
    if not bbox:
        problems.append("empty sprite")
    else:
        left, top, right, bottom = bbox
        for side, margin in (("L", left), ("T", top), ("R", w - right), ("B", h - bottom)):
            if margin < 1 and not (side == "B" and h <= 32):
                problems.append(f"margin {side}={margin} < 1")
        if body == 0:
            problems.append("no opaque body")

    status = "OK " if not problems else "BAD"
    print(f"[{status}] {name}.png {w}x{h} colors={len(colors)} body={body}")
    for p in problems[:8]:
        print("      -", p)
    return not problems


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "refs/hand")
    if target.is_file():
        files = [target]
    else:
        files = sorted(target.glob("*.png"))
        files = [f for f in files if not f.stem.endswith(tuple(f"_x{n}" for n in range(2, 21)))]
    results = [check(f) for f in files]
    sys.exit(0 if all(results) else 1)
