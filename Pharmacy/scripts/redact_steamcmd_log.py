"""把 steamcmd 日志里 +login<账号><密码> 的密码部分替换成 REDACTED。"""
import re
import sys
from pathlib import Path

PATTERN = re.compile(r"(\+login<[^<>]*><)[^<>]*>")


def redact(path: Path) -> int:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="surrogateescape")
    new, n = PATTERN.subn(r"\1REDACTED>", text)
    if n:
        path.write_bytes(new.encode("utf-8", errors="surrogateescape"))
    return n


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.is_file():
            print(f"skip (missing): {p}")
            continue
        print(f"{p}: {redact(p)} occurrence(s) redacted")
