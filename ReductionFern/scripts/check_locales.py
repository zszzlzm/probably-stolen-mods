#!/usr/bin/env python3
"""检查本地化文件：语言包之间 key 是否一致、代码里用到的 key 是否都在、有没有重复或空值。

用法：python scripts/check_locales.py
返回码非 0 表示有问题。
"""
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOC = ROOT / "mod" / "Localization"
SRC = ROOT / "src"


def load(path):
    rows = {}
    dupes = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip():
                continue
            key = row[0].strip()
            value = row[1] if len(row) > 1 else ""
            if key in rows:
                dupes.append(key)
            rows[key] = value
    return rows, dupes


def main():
    files = sorted(LOC.glob("*.csv"))
    if len(files) < 2:
        print("FAIL: need at least 2 locale files, found %d" % len(files))
        return 1

    locales = {}
    failed = False
    for path in files:
        rows, dupes = load(path)
        locales[path.stem] = rows
        print("%-6s %3d keys" % (path.stem, len(rows)))
        if dupes:
            failed = True
            print("  FAIL duplicate keys: %s" % ", ".join(sorted(set(dupes))))
        empty = sorted(k for k, v in rows.items() if not v.strip())
        if empty:
            failed = True
            print("  FAIL empty values: %s" % ", ".join(empty))

    names = list(locales)
    base = names[0]
    for other in names[1:]:
        missing = sorted(set(locales[base]) - set(locales[other]))
        extra = sorted(set(locales[other]) - set(locales[base]))
        if missing or extra:
            failed = True
            if missing:
                print("FAIL %s missing keys: %s" % (other, ", ".join(missing)))
            if extra:
                print("FAIL %s extra keys: %s" % (other, ", ".join(extra)))

    used = set()
    for path in SRC.rglob("*.cs"):
        text = path.read_text(encoding="utf-8")
        used.update(re.findall(r'Text\.Get\("([^"]+)"\)', text))
    unknown = sorted(used - set(locales[base]))
    unused = sorted(set(locales[base]) - used)
    if unknown:
        failed = True
        print("FAIL keys used in code but missing from %s: %s" % (base, ", ".join(unknown)))
    if unused:
        print("note: declared but not referenced from code: %s" % ", ".join(unused))

    print("OK" if not failed else "FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
