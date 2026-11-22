#!/usr/bin/env python3
"""给本地 mod 写一条 ModTrust 记录（省掉游戏里手动「审核并启用」）。

用法：
    python tools/trust_local.py --folder "<游戏>/Mods/<ModFolder>" --id harness.xxx --dll Xxx.dll [--no-order]
    python tools/trust_local.py ... --save-dir "%LOCALAPPDATA%\\Low\\Questing Goose Studio\\Probably Stolen"

做的事：
  1. 算 manifestHash / files / combinedHash / folderHash（与 ModTrust.ModFingerprint 一致）；
  2. 在 SaveFile.es3 的 modTrust 里替换同 id 记录，删掉 modTrustMac 让它重算；
  3. 默认把 id 追加进 modOrder（--no-order 可跳过）。

只在游戏关闭时跑：SaveFile.es3 会被游戏覆写。
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import sys

DEFAULT_SAVE_DIR = os.path.join(
    os.environ.get("USERPROFILE", os.path.expanduser("~")),
    "AppData",
    "LocalLow",
    "Questing Goose Studio",
    "Probably Stolen",
)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, help="Mods/<folder> 的绝对路径")
    ap.add_argument("--id", required=True)
    ap.add_argument("--dll", required=True)
    ap.add_argument("--no-order", action="store_true")
    ap.add_argument("--save-dir", default=os.environ.get("PS_SAVE_DIR", DEFAULT_SAVE_DIR),
                    help="存档目录（默认 %%LOCALAPPDATA%%\\Low\\Questing Goose Studio\\Probably Stolen）")
    args = ap.parse_args()

    folder = os.path.abspath(args.folder)
    manifest_path = os.path.join(folder, "manifest.xml")
    dll_path = os.path.join(folder, args.dll)
    for p in (manifest_path, dll_path):
        if not os.path.isfile(p):
            print("missing:", p)
            return 1

    manifest_hash = sha_file(manifest_path)
    dll_hash = sha_file(dll_path)
    combined = hashlib.sha256((manifest_hash + "\n" + args.dll + "|" + dll_hash).encode("utf-8")).hexdigest()

    excluded = {os.path.normcase(manifest_path), os.path.normcase(dll_path)}
    entries = []
    for dirpath, _dirnames, filenames in os.walk(folder):
        for name in filenames:
            full = os.path.normcase(os.path.abspath(os.path.join(dirpath, name)))
            if full in excluded:
                continue
            rel = os.path.relpath(full, folder).replace("\\", "/")
            entries.append(rel + "|" + sha_file(full))
    entries.sort()
    folder_hash = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()

    save = os.path.join(args.save_dir, "SaveFile.es3")
    if not os.path.isfile(save):
        print("missing:", save)
        return 1
    with io.open(save, encoding="utf-8") as f:
        data = json.load(f)

    if not args.no_order:
        order = data["modOrder"]["value"]
        if args.id not in order:
            order.append(args.id)
            print("modOrder += " + args.id, "| count:", len(order))
        else:
            print("modOrder already has", args.id)

    store = json.loads(data["modTrust"]["value"])
    sample = store["records"][0] if store["records"] else {}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"
    record = {
        "id": args.id,
        "source": "Local",
        "workshopId": "0",
        "manifestHash": manifest_hash,
        "files": [args.dll + "|" + dll_hash],
        "combinedHash": combined,
        "folderHash": folder_hash,
        "declared": [],
        "detected": [],
        "gameVersion": sample.get("gameVersion", ""),
        "approvedAt": now,
        "updatedAt": now,
        "developerMode": False,
        "scannerVersion": 4,
    }
    store["records"] = [r for r in store["records"] if r.get("id") != args.id]
    store["records"].append(record)
    data["modTrust"]["value"] = json.dumps(store, ensure_ascii=False, separators=(",", ":"))
    data.pop("modTrustMac", None)

    tmp = save + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, save)

    print("trusted:", args.id)
    print("  combined:", combined)
    print("  folderHash:", folder_hash, "files:", len(entries), "records:", len(store["records"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
