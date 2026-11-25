"""Dump Probably Stolen localization tables (key -> text) from Addressables bundles.

Usage:
    PYTHONPATH=tmp/pylibs python tools/extract_loc.py                # -> refs/loc_zh.json + refs/loc_en.json
    PYTHONPATH=tmp/pylibs python tools/extract_loc.py --lang zh --grep 化学
    PYTHONPATH=tmp/pylibs python tools/extract_loc.py --lang zh --key mech_chemical_supplies_unpack_warning

Unity Localization stores keys and values in two places:
  * localization-assets-shared_*.bundle  -> m_Entries: m_Id -> m_Key, per m_TableCollectionName
  * localization-string-tables-<locale>_*.bundle -> m_TableData: m_Id -> m_Localized
Ids are the join key, so this file merges both into {table: {key: text}}.
"""

import argparse
import json
import os
import re
import sys

BASE = r"F:/SteamLibrary/steamapps/common/Probably Stolen/Probably Stolen_Data/StreamingAssets/aa/StandaloneWindows64"
SHARED = "localization-assets-shared_assets_all.bundle"
LANGS = {
    "zh": "localization-string-tables-chinese(simplified)(zh)_assets_all.bundle",
    "en": "localization-string-tables-english(en)_assets_all.bundle",
}
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp", "loc")


def read_tables(bundle, value_field):
    import UnityPy

    env = UnityPy.load(os.path.join(BASE, bundle))
    out = {}
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = obj.read_typetree()
        rows = tree.get(value_field)
        if rows is None:
            continue
        name = tree.get("m_TableCollectionName") or tree.get("m_Name") or "?"
        name = re.sub(r"_(zh|en)$", "", name)  # value tables are named "<Table>_zh"
        table = out.setdefault(name, {})
        for row in rows:
            key = row.get("m_Key")
            if key is None:  # value table: key lives in the shared table
                table[row["m_Id"]] = row.get("m_Localized")
            else:
                table[key] = row.get("m_Localized")
    return out


def load(lang):
    import UnityPy  # noqa: F401  (fail early with a clear ImportError)

    keys = {}  # table -> {id: key}
    env = UnityPy.load(os.path.join(BASE, SHARED))
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = obj.read_typetree()
        rows = tree.get("m_Entries")
        if not rows:
            continue
        table = keys.setdefault(tree["m_TableCollectionName"], {})
        for row in rows:
            table[row["m_Id"]] = row["m_Key"]

    values = read_tables(LANGS[lang], "m_TableData")
    merged = {}
    for table, rows in values.items():
        keymap = keys.get(table, {})
        merged[table] = {keymap.get(i, str(i)): text for i, text in rows.items()}
    return merged


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=sorted(LANGS), default=None)
    ap.add_argument("--grep", default=None, help="regex over key or text")
    ap.add_argument("--key", default=None, help="exact key")
    ap.add_argument("--table", default=None, help="restrict to one table")
    args = ap.parse_args(argv)

    langs = [args.lang] if args.lang else sorted(LANGS)
    data = {lang: load(lang) for lang in langs}

    if not args.lang:  # dump mode
        os.makedirs(OUT_DIR, exist_ok=True)
        for lang, tables in data.items():
            path = os.path.join(OUT_DIR, "loc_%s.json" % lang)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(tables, fh, ensure_ascii=False, indent=1, sort_keys=True)
            total = sum(len(t) for t in tables.values())
            print("%s -> %s (%d keys in %d tables)" % (lang, path, total, len(tables)))
        return 0

    pattern = re.compile(args.grep, re.I) if args.grep else None
    hits = 0
    for table, rows in data[langs[0]].items():
        if args.table and table != args.table:
            continue
        for key, text in sorted(rows.items()):
            if args.key and key != args.key:
                continue
            if pattern and not (pattern.search(key) or pattern.search(text or "")):
                continue
            print("[%s] %s = %s" % (table, key, text))
            hits += 1
    if not hits:
        print("(no match)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
