import sys, os, re
import UnityPy

GAME = r"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data"
FILES = ["sharedassets0.assets", "resources.assets"]
OUT = r"C:\Users\zszzl\Documents\deepseek-harness\default-workspace\Pharmacy\refs"
os.makedirs(OUT, exist_ok=True)

KEYWORDS = sys.argv[1:] or ["dream_dust", "oxycodone_pill", "items_medical"]

found = []
for f in FILES:
    path = os.path.join(GAME, f)
    if not os.path.exists(path):
        continue
    print("loading", f, flush=True)
    env = UnityPy.load(path)
    for obj in env.objects:
        if obj.type.name not in ("Sprite", "Texture2D"):
            continue
        try:
            data = obj.read()
        except Exception:
            continue
        name = getattr(data, "m_Name", "") or ""
        low = name.lower()
        if any(k.lower() in low for k in KEYWORDS):
            found.append((f, obj.type.name, name, data))

print("matched", len(found))
for f, typ, name, data in found:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if typ == "Sprite":
        try:
            img = data.image
        except Exception as e:
            print("  sprite image failed", name, e)
            continue
        p = os.path.join(OUT, f"{safe}.png")
        img.save(p)
        print(f"  {typ:9} {name:40} {img.size} -> {p}")
    else:
        try:
            img = data.image
        except Exception:
            continue
        p = os.path.join(OUT, f"tex_{safe}.png")
        img.save(p)
        print(f"  {typ:9} {name:40} {img.size} -> {p}")
