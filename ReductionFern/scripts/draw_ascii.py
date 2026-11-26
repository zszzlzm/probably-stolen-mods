"""Render a 16xN palette-letter art grid to a sprite (no outline; draw_ascii adds it).

  python scripts/draw_ascii.py refs/art/fern.txt refs/final/restoring_fern.png
"""
import pathlib
import sys
from collections import deque

from PIL import Image

PAL = {
    "G": (0x3D, 0x82, 0x3F),
    "g": (0x41, 0x60, 0x3F),
    "T": (0x2F, 0x75, 0x6F),
    "B": (0x45, 0x91, 0x8B),
    "L": (0x8A, 0xBF, 0xBB),
    "D": (0x27, 0x56, 0x54),
    "C": (0xC5, 0xAC, 0x96),
    "M": (0x7D, 0x4F, 0x4A),
    "K": (0x29, 0x22, 0x34),
}
BG = (0, 0, 0, 3)


def outline(g):
    h, w = len(g), len(g[0])
    outside = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if g[y][x] == ".":
                outside[y][x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if g[y][x] == "." and not outside[y][x]:
                outside[y][x] = True
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not outside[ny][nx] and g[ny][nx] == ".":
                outside[ny][nx] = True
                q.append((nx, ny))
    out = [row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] != "." or not outside[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and g[ny][nx] != ".":
                    out[y][x] = "K"
                    break
    return out


def main():
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    rows = [r for r in src.read_text(encoding="utf-8").splitlines() if r.strip() or True]
    rows = [r for r in rows if not r.startswith("#")]
    w = max(len(r) for r in rows)
    g = [list(r.ljust(w, ".")) for r in rows]
    h = len(g)
    g = outline(g)

    img = Image.new("RGBA", (w, h), BG)
    for y in range(h):
        for x in range(w):
            if g[y][x] != ".":
                img.putpixel((x, y), PAL[g[y][x]] + (255,))
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    big = img.resize((w * 12, h * 12), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
    bg.alpha_composite(big)
    bg.save(dst.with_name(dst.stem + "_x12.png"))
    counts = {}
    for row in g:
        for c in row:
            if c != ".":
                counts[c] = counts.get(c, 0) + 1
    print(f"# {w}x{h} colors:", sorted(counts.items()))
    for row in g:
        print("".join(row))


if __name__ == "__main__":
    main()
