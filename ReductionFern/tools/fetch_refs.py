"""Download fern reference photos (web) for the local model.

Tries Huaban's JSON API first (the search page itself is JS-rendered), then falls
back to Wikimedia Commons (freely licensed botanicals).

  python tools/fetch_refs.py huaban
  python tools/fetch_refs.py commons
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
OUT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "web"
OUT.mkdir(parents=True, exist_ok=True)


def get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def save(name, data):
    p = OUT / name
    p.write_bytes(data)
    print("saved", p, len(data))
    return p


def huaban():
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://huaban.com/search?q=%E8%95%A8",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = json.dumps({"q": "蕨", "sort": "default", "limit": 20, "page": 1}).encode("utf-8")
    for url in ("https://huaban.com/v3/search/file", "https://huaban.com/api/search/file"):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            data = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore"))
        except Exception as e:
            print("huaban", url, "failed:", e)
            continue
        pins = data.get("pins") or data.get("data") or []
        urls = []
        for pin in pins:
            key = (pin.get("file") or {}).get("key") or pin.get("file_key")
            if key:
                urls.append(f"https://hbimg.huabanimg.com/{key}_fw658")
        print("huaban pins:", len(pins), "images:", len(urls))
        out = []
        for i, u in enumerate(urls[:8]):
            try:
                out.append(save(f"huaban_{i}.jpg", get(u)))
            except Exception as e:
                print("skip", u, e)
        return out
    return []


def commons():
    q = urllib.parse.quote("fern frond")
    api = (f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={q}"
           "&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=900&format=json")
    data = json.loads(get(api).decode("utf-8", "ignore"))
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for i, (_, page) in enumerate(pages.items()):
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        try:
            out.append(save(f"commons_{i}.jpg", get(url)))
        except Exception as e:
            print("skip", url, e)
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "commons"
    files = huaban() if mode == "huaban" else commons()
    print(f"# {len(files)} files in {OUT}")
