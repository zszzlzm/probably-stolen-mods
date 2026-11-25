"""Extract vanilla sprites from the game's Unity assets for art reference.

Usage:
    PS_GAME_DATA=... python extract_vanilla_sprites.py printer            # names containing "printer"
    PS_GAME_DATA=... python extract_vanilla_sprites.py items_tool2        # texture page containing the atlas
    PS_GAME_DATA=... python extract_vanilla_sprites.py --list items_tool2 # list sprite names on that page

Output goes to <mod>/refs/vanilla/ (git-ignored), never into mod/.
"""

import os
import re
import sys
from pathlib import Path

import UnityPy

GAME = os.environ.get(
    "PS_GAME_DATA",
    r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data",
)
FILES = ["sharedassets0.assets", "sharedassets1.assets", "resources.assets", "globalgamemanagers.assets"]
OUT = Path(os.environ.get("PS_SPRITE_OUT", Path(__file__).resolve().parents[1] / "refs" / "vanilla"))
OUT.mkdir(parents=True, exist_ok=True)


def safe(name):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", name)


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    list_only = "--list" in argv
    keywords = [a for a in argv if not a.startswith("--")]

    for fname in FILES:
        path = os.path.join(GAME, fname)
        if not os.path.exists(path):
            continue
        print("loading", fname, flush=True)
        env = UnityPy.load(path)
        pages = {}
        for obj in env.objects:
            if obj.type.name not in ("Sprite", "Texture2D"):
                continue
            try:
                data = obj.read()
            except Exception:
                continue
            name = getattr(data, "m_Name", "") or ""
            if obj.type.name == "Texture2D":
                pages[name] = data
                continue
            # Sprite: match by name, or by owning texture page name
            tex = getattr(getattr(data, "m_RD", None), "texture", None)
            tex_name = ""
            if tex is not None:
                try:
                    tex_name = tex.read().m_Name
                except Exception:
                    tex_name = ""
            hit = any(k.lower() in name.lower() for k in keywords) or any(
                k.lower() in tex_name.lower() for k in keywords
            )
            if not hit:
                continue
            if list_only:
                print(f"  SPRITE {name:38} tex={tex_name} rect={data.m_Rect}")
                continue
            try:
                img = data.image
            except Exception as e:
                print("  sprite image failed", name, e)
                continue
            p = OUT / f"{safe(tex_name or 'nopage')}__{safe(name)}.png"
            img.save(p)
            print(f"  {name:38} tex={tex_name:22} {img.size} -> {p.name}")

    if list_only:
        return 0

    # also dump the texture pages themselves (full atlas, useful for palette work)
    for fname in FILES:
        path = os.path.join(GAME, fname)
        if not os.path.exists(path):
            continue
        env = UnityPy.load(path)
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            try:
                data = obj.read()
            except Exception:
                continue
            name = getattr(data, "m_Name", "") or ""
            if not any(k.lower() in name.lower() for k in keywords):
                continue
            try:
                img = data.image
            except Exception:
                continue
            p = OUT / f"page_{safe(name)}.png"
            if not p.exists():
                img.save(p)
                print(f"  page {name:28} {img.size} -> {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
