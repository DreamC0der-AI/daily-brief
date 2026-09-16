#!/usr/bin/env python3
"""Collect candidate news items from RSS feeds into data/candidates/YYYY-MM-DD.json.

Usage: python collect.py [--date YYYY-MM-DD] [--hours 36] [--no-og]
"""
import argparse, concurrent.futures as cf, datetime as dt, hashlib, html, json, re, sys, time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import feedparser, requests

ROOT = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid", "src"}
TAG_RE = re.compile(r"<[^>]+>")
JUNK_TITLE = re.compile(r"promo code|coupon|discount code|referral deal|best deals|% off|\bdeals?\b.*\bsale\b", re.I)
IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)", re.I)
OG_RE = [re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I),
         re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I),
         re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', re.I)]


def clean_url(u):
    p = urlparse(u)
    q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in TRACKING]
    return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/"), "", urlencode(q), ""))


def norm_title(t):
    return re.sub(r"[^\w一-鿿]+", " ", t.lower()).strip()


def strip_html(s, limit=600):
    s = html.unescape(TAG_RE.sub(" ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


def entry_image(e):
    for m in e.get("media_content", []) + e.get("media_thumbnail", []):
        if m.get("url") and not m.get("medium", "image").startswith("video"):
            return m["url"]
    for l in e.get("links", []):
        if l.get("type", "").startswith("image") and l.get("href"):
            return l["href"]
    for k in ("content", "summary"):
        v = e.get(k)
        if isinstance(v, list):
            v = v[0].get("value", "")
        m = IMG_RE.search(v or "")
        if m:
            return m.group(1)
    return None


def entry_time(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    return dt.datetime(*t[:6], tzinfo=dt.timezone.utc)


def fetch_feed(topic, src):
    try:
        r = requests.get(src["url"], headers=UA, timeout=20)
        f = feedparser.parse(r.content)
        items = []
        for e in f.entries:
            link = e.get("link")
            title = (e.get("title") or "").strip()
            if not link or not title or JUNK_TITLE.search(title):
                continue
            body = e.get("summary", "")
            if e.get("content"):
                body = e["content"][0].get("value", body)
            items.append({
                "topic": topic, "source": src["name"], "lang": src["lang"], "weight": src.get("weight", 1.0),
                "title": strip_html(title, 300), "url": link, "canonical": clean_url(link),
                "published": entry_time(e), "excerpt": strip_html(body), "image": entry_image(e),
                "comments": e.get("comments"),
            })
        return src["name"], items, None
    except Exception as ex:
        return src["name"], [], f"{type(ex).__name__}: {ex}"


def og_image(url):
    try:
        r = requests.get(url, headers=UA, timeout=12, stream=True)
        head = r.raw.read(200_000, decode_content=True).decode("utf-8", "ignore")
        for rx in OG_RE:
            m = rx.search(head)
            if m:
                return html.unescape(m.group(1))
    except Exception:
        pass
    return None


def score(item, now):
    age_h = (now - item["published"]).total_seconds() / 3600 if item["published"] else 24
    recency = max(0.0, 1.0 - age_h / 48)
    return round(item["weight"] * (0.5 + recency) + (0.3 if item["image"] else 0), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--hours", type=int, default=36)
    ap.add_argument("--no-og", action="store_true", help="skip og:image page fetches")
    args = ap.parse_args()
    t0 = time.time()
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=args.hours)
    feeds = json.loads((ROOT / "feeds.json").read_text())
    jobs = [(topic, src) for topic, srcs in feeds.items() for src in srcs]

    with cf.ThreadPoolExecutor(12) as ex:
        results = list(ex.map(lambda j: fetch_feed(*j), jobs))

    errors, raw = {}, []
    for name, items, err in results:
        if err:
            errors[name] = err
        raw.extend(items)

    # Keep recent; undated feeds get a synthetic timestamp so they are not dropped.
    fresh = []
    for it in raw:
        if it["published"] is None:
            it["published"] = now - dt.timedelta(hours=12)
            it["undated"] = True
        if it["published"] >= cutoff:
            fresh.append(it)

    # Dedupe by canonical URL, then by normalized title.
    seen_url, seen_title, items = set(), set(), []
    for it in sorted(fresh, key=lambda x: -x["weight"]):
        nt = norm_title(it["title"])
        if it["canonical"] in seen_url or nt in seen_title:
            continue
        seen_url.add(it["canonical"]); seen_title.add(nt)
        items.append(it)

    # Cap items per source so bulk feeds (arXiv) do not swamp a topic.
    per_src = Counter(); capped = []
    for it in sorted(items, key=lambda x: x["published"], reverse=True):
        cap = 8 if it["source"].startswith("arXiv") else 20
        if per_src[it["source"]] < cap:
            per_src[it["source"]] += 1; capped.append(it)
    items = capped

    # Fill missing images via og:image (bounded), then drop images shared by >=3 items of one source (logos).
    if not args.no_og:
        need = [it for it in items if not it["image"]][:120]
        with cf.ThreadPoolExecutor(16) as ex:
            for it, img in zip(need, ex.map(lambda i: og_image(i["url"]), need)):
                it["image"] = img
    counts = Counter((it["source"], it["image"]) for it in items if it["image"])
    for it in items:
        if it["image"] and counts[(it["source"], it["image"])] >= 3:
            it["image"] = None

    for it in items:
        it["score"] = score(it, now)
        it["published"] = it["published"].isoformat()
        it["id"] = hashlib.sha1(it["canonical"].encode()).hexdigest()[:10]
        del it["weight"]
    items.sort(key=lambda x: (x["topic"], -x["score"]))

    out = {
        "date": args.date, "generated_at": now.isoformat(), "window_hours": args.hours,
        "counts": dict(Counter(it["topic"] for it in items)), "with_image": sum(1 for it in items if it["image"]),
        "errors": errors, "items": items,
    }
    path = ROOT / "data" / "candidates" / f"{args.date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"wrote {path}: {len(items)} items {out['counts']} images={out['with_image']} "
          f"errors={len(errors)} in {time.time()-t0:.1f}s")
    for k, v in errors.items():
        print(f"  ! {k}: {v}", file=sys.stderr)


if __name__ == "__main__":
    main()
