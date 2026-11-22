"""Show exactly which images were handed to the model as references."""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
items = [
    (ROOT / "refs" / "web" / "web_02.jpg", "web ref: real fern frond (Bing image search)"),
    (ROOT / "refs" / "model" / "hydroreed_filter_ref.png", "game ref: hydroreed_filter 16x32, x16"),
    (ROOT / "refs" / "model" / "dream_cap_ref.png", "game ref: dream_cap 16x32, x16"),
    (ROOT / "refs" / "model" / "hydroreed_p_ref.png", "game ref: hydroreed_p 48x64, x16"),
]

thumbs = []
for p, label in items:
    im = Image.open(p).convert("RGBA")
    im.thumbnail((360, 360))
    thumbs.append((im, label))

pad = 16
w = max(t[0].width for t in thumbs) + pad * 2
h = sum(t[0].height + 40 + pad for t in thumbs) + pad
sheet = Image.new("RGBA", (w, h), (28, 30, 34, 255))
d = ImageDraw.Draw(sheet)
y = pad
for im, label in thumbs:
    sheet.alpha_composite(im, (pad, y))
    d.text((pad, y + im.height + 6), label, fill=(210, 220, 230, 255))
    y += im.height + 40 + pad
out = ROOT / "refs" / "refs_used.png"
sheet.save(out)
print(out, sheet.size)
