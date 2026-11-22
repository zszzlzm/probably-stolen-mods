"""Print a vanilla sprite as an ASCII grid with palette letters (for hand-laying)."""
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
LETTER = {
    (0x29, 0x22, 0x34): "K", (0x27, 0x56, 0x54): "D", (0x2F, 0x75, 0x6F): "T",
    (0x45, 0x91, 0x8B): "B", (0x8A, 0xBF, 0xBB): "L", (0x3D, 0x82, 0x3F): "G",
    (0x41, 0x60, 0x3F): "g", (0xC5, 0xAC, 0x96): "C", (0x7D, 0x4F, 0x4A): "M",
    (0xA4, 0x71, 0x5D): "m", (0x79, 0x74, 0x6E): "n", (0x88, 0x94, 0x8A): "h",
    (0x64, 0x34, 0x3B): "p", (0x8F, 0x6B, 0x5A): "q", (0xB6, 0x8B, 0x74): "r",
    (0xD5, 0xD2, 0xB8): "w", (0x64, 0x53, 0x55): "u",
}


def show(path):
    im = Image.open(path).convert("RGBA")
    print(f"== {path.name} {im.size}")
    for y in range(im.height):
        row = []
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a <= 8:
                row.append(".")
            else:
                row.append(LETTER.get((r, g, b), "?"))
        print("".join(row))


if __name__ == "__main__":
    for name in sys.argv[1:]:
        p = pathlib.Path(name)
        if not p.exists():
            p = ROOT / "refs" / "vanilla" / f"{name}__resources.png"
        show(p)
