"""Bing image search downloader (fallback for fern references)."""
import html
import json
import pathlib
import re
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
OUT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "web"
OUT.mkdir(parents=True, exist_ok=True)
QUERY = "fern frond botanical"


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def main():
    url = "https://www.bing.com/images/search?" + urllib.parse.urlencode({"q": QUERY, "form": "HDRSC2", "first": "1"})
    page = get(url).decode("utf-8", "ignore")
    print("page bytes", len(page))
    murls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', page)
    if not murls:
        murls = re.findall(r'"murl":"(.*?)"', page)
    print("murls", len(murls))
    n = 0
    for u in murls:
        u = html.unescape(u).replace("\\/", "/")
        if not u.startswith("http"):
            continue
        try:
            data = get(u)
        except Exception as e:
            print("dl fail", u[:80], e)
            continue
        if len(data) < 8000:
            continue
        (OUT / f"web_{n:02d}.jpg").write_bytes(data)
        print("saved", n, len(data), u[:100])
        n += 1
        if n >= 8:
            break
    print("total", n)


if __name__ == "__main__":
    main()
