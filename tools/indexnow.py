#!/usr/bin/env python3
"""
Tell Bing (and other IndexNow search engines) about new or updated ENYT pages,
so new stories can show up in Bing and in ChatGPT search sooner.

    python3 tools/indexnow.py                 # pages in news-sitemap.xml
    python3 tools/indexnow.py /about/ /cb5meetings/

The key file <key>.txt must stay in the repo root. https://www.indexnow.org/
"""
import glob, json, os, re, sys, urllib.request

HOST = "eastnewyorktimes.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key():
    for path in glob.glob(os.path.join(ROOT, "*.txt")):
        name = os.path.basename(path)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name) and open(path).read().strip() == name:
            return name
    sys.exit("No IndexNow key file found in the repo root.")


def main():
    urls = [f"https://{HOST}{a if a.startswith('/') else '/' + a}" for a in sys.argv[1:]]
    if not urls:
        with open(os.path.join(ROOT, "news-sitemap.xml"), encoding="utf-8") as fh:
            urls = re.findall(r"<loc>(.*?)</loc>", fh.read())
        if urls:
            urls += [f"https://{HOST}/", f"https://{HOST}/stories/", f"https://{HOST}/feed.xml"]
    if not urls:
        print("IndexNow: nothing new to report.")
        return 0
    k = key()
    body = json.dumps({"host": HOST, "key": k, "keyLocation": f"https://{HOST}/{k}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow: HTTP {resp.status} for {len(urls)} URL(s)")
    except urllib.error.HTTPError as err:
        # Never fail the sitemap job over a ping.
        print(f"IndexNow: HTTP {err.code} {err.reason}")
    for u in urls:
        print("  " + u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
