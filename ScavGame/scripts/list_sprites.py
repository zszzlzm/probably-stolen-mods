"""列出 Probably Stolen 里的 Sprite 名称，按关键词筛选，方便挑封面参考素材。"""
import os
import sys

import UnityPy

GAME = r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data"
FILES = ["sharedassets0.assets", "resources.assets", "sharedassets1.assets"]

KEYWORDS = [k.lower() for k in (sys.argv[1:] or ["scrap", "junk", "trash", "crate", "debris", "wreck"])]

names = []
for f in FILES:
    path = os.path.join(GAME, f)
    if not os.path.exists(path):
        continue
    env = UnityPy.load(path)
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        try:
            data = obj.read()
        except Exception:
            continue
        name = getattr(data, "m_Name", "") or ""
        if any(k in name.lower() for k in KEYWORDS):
            names.append((f, name))

print(f"matched {len(names)}")
for f, n in sorted(names):
    print(f"{f}\t{n}")
