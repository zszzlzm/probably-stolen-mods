"""Turn a finished sprite into a magenta-backed, 16x reference image for the model.

    python scripts/make_sprite_ref.py refs/final/restoring_fern_l.png

The model needs references that look like pixel art, not like smoothed renders: the
sprite is upscaled with nearest neighbour and padded onto flat magenta, the same way
``make_refs.py`` prepares the vanilla sprites.
"""
import pathlib
import sys

from PIL import Image

SCALE = 16
PAD = 32


def main():
    src = pathlib.Path(sys.argv[1])
    out = src.parent.parent / "model" / (src.stem + "_ref.png")
    img = Image.open(src).convert("RGBA")
    big = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
    canvas = Image.new("RGB", (big.width + PAD * 2, big.height + PAD * 2), (255, 0, 255))
    canvas.paste(big, (PAD, PAD), big)
    canvas.save(out)
    print(out)


if __name__ == "__main__":
    main()
