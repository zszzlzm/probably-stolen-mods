"""从游戏资源里导出指定 Sprite（含图集切图）为 PNG，供生图模型当参考图。"""
import os
import sys

from PIL import Image
import UnityPy

GAME = r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data"
FILES = ["resources.assets", "sharedassets0.assets", "sharedassets1.assets"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "refs", "game")

WANT = sys.argv[1:] or [
    "debris_pile1", "debris_pile2", "debris_pile3", "trash_pile",
    "scrap_metal", "scrap_metal_2", "ruined_machine_medium2",
    "ruined_machine_small", "working_pipes",
]

os.makedirs(OUT, exist_ok=True)
wanted = {w.lower() for w in WANT}
saved = 0

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
        name = (getattr(data, "m_Name", "") or "")
        if name.lower() not in wanted:
            continue
        try:
            img = data.image
        except Exception as exc:  # 图集切图失败时跳过
            print("skip", name, exc)
            continue
        dst = os.path.join(OUT, f"{name}.png")
        img.save(dst)
        print(f"{name:28s} {img.width}x{img.height}  -> {dst}")
        saved += 1

print("saved", saved)
