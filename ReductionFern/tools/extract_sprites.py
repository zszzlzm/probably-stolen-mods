"""Extract vanilla plant sprites from the game's Unity assets.

Usage:
  python extract_sprites.py list                 # print matching sprite metadata
  python extract_sprites.py dump <outdir>        # write PNGs + metadata.json

Sprites are sub-assets of multi-sprite textures (e.g. Items/items_hydroponic_plant),
so we read every Sprite object and keep the ones whose name matches TARGETS.
"""
import json
import os
import sys

import UnityPy

GAME = r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data"
FILES = ["resources.assets", "sharedassets0.assets", "sharedassets1.assets"]
TARGETS = ["hydroreed", "dream_cap", "coffee_bean", "restoring", "fern",
           "fillerweed", "kotton_plant", "nutrifruit"]


def iter_sprites():
    for fname in FILES:
        path = os.path.join(GAME, fname)
        env = UnityPy.load(path)
        for obj in env.objects:
            if obj.type.name != "Sprite":
                continue
            try:
                sprite = obj.read()
            except Exception:
                continue
            name = sprite.m_Name or ""
            low = name.lower()
            if not any(t in low for t in TARGETS):
                continue
            try:
                tex = sprite.m_RD.texture.read()
                tex_name = tex.m_Name
                tex_size = (tex.m_Width, tex.m_Height)
            except Exception:
                tex_name, tex_size = "?", (0, 0)
            rect = sprite.m_Rect
            yield {
                "file": fname,
                "name": name,
                "texture": tex_name,
                "texture_size": tex_size,
                "rect": [rect.x, rect.y, rect.width, rect.height],
                "pivot": [sprite.m_Pivot.x, sprite.m_Pivot.y],
                "pixels_to_units": sprite.m_PixelsToUnits,
                "sprite": sprite,
            }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    if mode == "list":
        rows = []
        for s in iter_sprites():
            rows.append({k: s[k] for k in ("file", "name", "texture", "texture_size", "rect", "pivot", "pixels_to_units")})
        rows.sort(key=lambda r: (r["name"], r["file"]))
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
        print(f"# {len(rows)} sprites")
        return

    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta = []
    for s in iter_sprites():
        image = s["sprite"].image
        if image is None:
            continue
        base = f"{s['name']}__{s['file'].replace('.assets', '')}"
        png = os.path.join(outdir, base + ".png")
        image.save(png)
        meta.append({
            "png": os.path.basename(png),
            "file": s["file"],
            "name": s["name"],
            "texture": s["texture"],
            "texture_size": s["texture_size"],
            "rect": s["rect"],
            "pivot": s["pivot"],
            "pixels_to_units": s["pixels_to_units"],
            "size": list(image.size),
        })
    meta.sort(key=lambda m: (m["name"], m["file"]))
    with open(os.path.join(outdir, "sprites.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    print(f"# wrote {len(meta)} sprites to {outdir}")


if __name__ == "__main__":
    main()
