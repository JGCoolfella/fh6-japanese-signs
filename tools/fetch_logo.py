"""Search / download logos from Wikimedia Commons or English Wikipedia (polite, with retries).

  python tools/fetch_logo.py search "ENEOS logo"
  python tools/fetch_logo.py get "File:ENEOS logo.svg" eneos_logo.png [width]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "fh6-personal-mod/1.0 (personal offline game mod; contact via local user)"}
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
SITES = ["https://commons.wikimedia.org/w/api.php", "https://en.wikipedia.org/w/api.php"]


def api(site, **params):
    params["format"] = "json"
    url = site + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # rate limits and hiccups: back off
            time.sleep(3 * (attempt + 1))
            err = e
    raise RuntimeError(f"api failed: {err}")


def search(q):
    for site in SITES:
        res = api(site, action="query", list="search", srnamespace=6, srlimit=8, srsearch=q)
        for r in res.get("query", {}).get("search", []):
            print(("commons " if "commons" in site else "enwiki  ") + r["title"])
        time.sleep(1.5)


def get(title, out, width=1600):
    for site in SITES:
        res = api(site, action="query", prop="imageinfo", titles=title, iiprop="url|size|extmetadata", iiurlwidth=width)
        page = list(res["query"]["pages"].values())[0]
        if "imageinfo" not in page:
            continue
        ii = page["imageinfo"][0]
        url = ii.get("thumburl") or ii["url"]
        lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
        for attempt in range(6):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                    data = r.read()
                if data[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"GIF8") or data[:3] == b"\xff\xd8\xff":
                    open(os.path.join(ASSETS, out), "wb").write(data)
                    print(f"saved {out} from {'commons' if 'commons' in site else 'enwiki'} ({lic})")
                    return
            except Exception:
                pass
            time.sleep(3 * (attempt + 1))
        raise RuntimeError("download failed")
    raise RuntimeError(f"not found: {title}")


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search(sys.argv[2])
    else:
        get(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 1600)
