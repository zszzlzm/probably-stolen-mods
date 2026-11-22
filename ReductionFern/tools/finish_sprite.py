"""Finish a downscaled sprite: keep a 1px margin on every side, then add the 1px dark outline.

  python tools/finish_sprite.py refs/pix/fern_203.png refs/final/restoring_fern.png
"""
import pathlib
import sys

from PIL import Image

K = (0x29, 0x22, 0x34, 255)


def finish(src, dst):
    src = pathlib.Path(src)
    dst = pathlib.Path(dst)
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    transparent = img.getchannel("A").point(lambda a: 255 if a <= 8 else 0)
    bb = transparent.getbbox()
    if bb is None:
        raise SystemExit("sprite is empty")
    # bb = (left, upper, right, lower) of the *transparent* area; we want the
    # content to start at 2px so the outline pass leaves a 1px margin.
    left, upper, right, lower = bb
    dx = 2 - (left if left > 0 else 0) if left > 0 else 0
    # simpler: measure the content bbox, shift so its min sits at 2
    content = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    cx0, cy0, cx1, cy1 = content
    dx = 2 - cx0 if cx0 < 2 else 0
    dy = 2 - cy0 if cy0 < 2 else 0
    if dx or dy:
        shifted = Image.new("RGBA", (w, h), (0, 0, 0, 3))
        shifted.paste(img, (dx, dy), img)
        img = shifted

    px = img.load()
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 8:
                continue
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + ddx, y + ddy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 8:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = K

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    big = img.resize((w * 12, h * 12), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (26, 28, 32, 255))
    bg.alpha_composite(big)
    bg.save(dst.with_name(dst.stem + "_x12.png"))
    print(f"# {dst} {w}x{h}")


if __name__ == "__main__":
    finish(sys.argv[1], sys.argv[2])
