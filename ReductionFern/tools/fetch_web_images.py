"""Download fern reference photos through Baidu image search (works where huaban/wikimedia block us)."""
import json
import pathlib
import re
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
OUT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "web"
OUT.mkdir(parents=True, exist_ok=True)

QUERIES = ["蕨类植物", "蕨叶 手绘", "fern frond"]


def fetch(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def search(word):
    params = {
        "tn": "resultjson_com", "logid": "123", "ipn": "rj", "ct": "201326592",
        "is": "", "fp": "result", "fr": "", "word": word, "queryWord": word,
        "cl": "2", "lm": "-1", "ie": "utf-8", "oe": "utf-8", "st": "-1",
        "z": "", "ic": "0", "hd": "1", "latest": "", "cro": "",
        "pn": "0", "rn": "12", "gsm": "1e",
    }
    url = "https://image.baidu.com/search/acjson?" + urllib.parse.urlencode(params)
    raw = fetch(url, {"User-Agent": UA, "Referer": "https://image.baidu.com/"}).decode("utf-8", "ignore")
    try:
        data = json.loads(raw)
    except Exception:
        fixed = re.sub(r",\s*}", "}", raw).replace("\\'", "'")
        data = json.loads(fixed)
    return data.get("data") or []


def main():
    got = 0
    for q in QUERIES:
        try:
            items = search(q)
        except Exception as e:
            print("search failed", q, e)
            continue
        for it in items:
            url = it.get("hoverURL") or it.get("middleURL") or it.get("thumbURL")
            if not url or not url.startswith("http"):
                continue
            try:
                data = fetch(url)
            except Exception as e:
                print("dl fail", e)
                continue
            if len(data) < 8000:
                continue
            p = OUT / f"web_{got:02d}.jpg"
            p.write_bytes(data)
            print("saved", p.name, len(data), q)
            got += 1
            if got >= 8:
                return
    print("total", got)


if __name__ == "__main__":
    main()
