#!/usr/bin/env python3
"""Fetch readable article text for candidate ids into data/fetched/DATE.txt (gitignored), for the editor to Read.

Usage:
  .venv/bin/python fetch.py ID [ID ...]            # overwrite today's fetch file
  .venv/bin/python fetch.py --append ID [ID ...]   # add to it
  .venv/bin/python fetch.py --cap 5000 ID ...      # characters kept per article (default 3500)
Ids are looked up across all data/candidates/*.json files. A full URL may be given instead of an id.
Only a one-line-per-article summary is printed; read the output file for the text.
"""
import argparse, concurrent.futures as cf, datetime as dt, glob, html, json, re
from pathlib import Path

import requests

ROOT = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
DROP = re.compile(r"<(script|style|nav|header|footer|aside|figure|noscript)[^>]*>.*?</\1>", re.S | re.I)
PARA = re.compile(r"<(?:p|h2|li)[^>]*>(.*?)</(?:p|h2|li)>", re.S | re.I)
NOISE = ("newsletter", "sign up", "subscribe", "cookie", "all rights reserved")


def candidates():
    cand = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "candidates" / "*.json"))):
        for it in json.loads(Path(f).read_text())["items"]:
            cand[it["id"]] = it
    return cand


def grab(url, cap):
    try:
        t = requests.get(url, headers=UA, timeout=20).text
        t = DROP.sub("", t)
        ps = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", p))).strip() for p in PARA.findall(t)]
        ps = [p for p in ps if len(p) > 50 and not any(n in p.lower() for n in NOISE)]
        return "\n".join(ps)[:cap]
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--cap", type=int, default=3500)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    cand = candidates()
    jobs = []
    for i in a.ids:
        if i.startswith("http"):
            jobs.append({"id": "-", "source": "", "title": i, "url": i, "excerpt": "", "image": None, "published": ""})
        elif i in cand:
            jobs.append(cand[i])
        else:
            print(f"unknown id: {i}")
    out = ROOT / "data" / "fetched" / f"{a.date}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(8) as ex:
        texts = list(ex.map(lambda it: grab(it["url"], a.cap), jobs))
    with open(out, "a" if a.append else "w") as fh:
        for it, txt in zip(jobs, texts):
            fh.write(f"\n######## [{it['id']}] {it['source']} | {it['title']}\nURL {it['url']}  IMG {'Y' if it.get('image') else '-'}  "
                     f"{(it.get('published') or '')[:10]}\nEXCERPT: {(it.get('excerpt') or '')[:400]}\nTEXT({len(txt)}):\n{txt}\n")
            print(f"{it['id']:12} {len(txt):5} chars  {it['title'][:70]}")
    print("wrote", out)


if __name__ == "__main__":
    main()
