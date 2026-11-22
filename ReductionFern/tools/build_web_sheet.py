import pathlib

from PIL import Image, ImageDraw

WEB = pathlib.Path(__file__).resolve().parent.parent / "refs" / "web"
files = sorted(WEB.glob("web_*.jpg"))
thumbs = []
for p in files:
    im = Image.open(p).convert("RGB")
    im.thumbnail((280, 280))
    thumbs.append((p.name, im))

cols = 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 300, rows * 320), (28, 30, 34))
d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(thumbs):
    x, y = (i % cols) * 300 + 10, (i // cols) * 320 + 10
    sheet.paste(im, (x, y))
    d.text((x, y + 290), name, fill=(210, 220, 230))
out = WEB / "web_sheet.png"
sheet.save(out)
print(out, sheet.size)
