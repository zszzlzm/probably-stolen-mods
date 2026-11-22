"""从 mod/preview.png（1280x720）生成包内用的 640x360 缩略图。"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = ROOT / "mod" / "preview.png"
dst = ROOT / "build" / "preview_640.png"
img = Image.open(src).convert("RGB")
small = img.resize((640, 360), Image.LANCZOS)
small.save(dst, "PNG", optimize=True)
print("wrote", dst, dst.stat().st_size, "bytes", small.size)
