import json
import os

import UnityPy

GAME = r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data"
rows = []
for f in ["resources.assets", "sharedassets0.assets", "sharedassets1.assets"]:
    env = UnityPy.load(os.path.join(GAME, f))
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        d = obj.read()
        n = d.m_Name or ""
        r = d.m_Rect
        rows.append((n, int(r.width), int(r.height), f))

seen, out = set(), []
for n, w, h, f in sorted(rows):
    key = (n, w, h)
    if key in seen:
        continue
    seen.add(key)
    out.append(f"{n} {w}x{h}")
open("refs/all_sprites.txt", "w", encoding="utf-8").write("\n".join(out))
print(len(out))
