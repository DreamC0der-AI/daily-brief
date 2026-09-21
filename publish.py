#!/usr/bin/env python3
"""Validate, hydrate, build and publish a digest. This is the ONLY command needed after writing digests/DATE.json.

Usage:
  .venv/bin/python publish.py                 # today's digest: validate, build, commit, push
  .venv/bin/python publish.py --date 2026-09-21
  .venv/bin/python publish.py --no-push       # validate + build only (local preview in site/)
  .venv/bin/python publish.py --wait          # also wait for the GitHub Pages deploy and check the live page

The digest file is plain data written by the editor (Claude Code) with the file-writing tool. Each item needs only:
  id, kind ("long"|"short"), topic, title_en, title_zh, summary_en, summary_zh  (+ optional why_en/why_zh, source, url, image)
`summary_*` may be a string or a LIST of paragraphs (preferred for long items; joined with blank lines here).
Missing url / source / image / topic are filled in from the candidates files by id.
"""
import argparse, datetime as dt, glob, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = "DreamC0der-AI/daily-brief"
GH_USER = "DreamC0der-AI"
SITE_URL = "https://dreamc0der-ai.github.io/daily-brief/"
TOPICS = {"ai", "tech", "crypto", "bio"}
GIT_ID = ["-c", "user.name=James Sun", "-c", "user.email=akagishigerutokyo@gmail.com"]
TRAILER = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"


def load_candidates():
    cand = {}
    for f in sorted(glob.glob(str(ROOT / "data" / "candidates" / "*.json"))):
        for it in json.loads(Path(f).read_text())["items"]:
            cand[it["id"]] = it
    return cand


def hydrate(d, cand):
    for it in d["items"]:
        c = cand.get(it.get("id"), {})
        for k in ("url", "source", "topic"):
            if not it.get(k) and c.get(k):
                it[k] = c[k]
        if "image" not in it:
            it["image"] = c.get("image")
        for k in ("summary_en", "summary_zh"):
            if isinstance(it.get(k), list):
                it[k] = "\n\n".join(p.strip() for p in it[k] if p and p.strip())
        for k, v in list(it.items()):
            if isinstance(v, str):
                it[k] = v.strip()
    return d


def validate(d, date, cand):
    errors, warns = [], []
    if d.get("date") != date:
        errors.append(f'"date" is {d.get("date")!r}, expected {date!r}')
    for k in ("intro_en", "intro_zh"):
        if not d.get(k):
            warns.append(f"missing {k}")
    seen = set()
    for n, it in enumerate(d.get("items", []), 1):
        tag = f'item {n} ({it.get("id", "?")})'
        if not it.get("id"):
            errors.append(f"{tag}: missing id")
        elif it["id"] in seen:
            errors.append(f"{tag}: duplicate id")
        seen.add(it.get("id"))
        if it.get("id") and it["id"] not in cand and not it.get("url"):
            errors.append(f"{tag}: id not found in any candidates file and no url given")
        if it.get("kind") not in ("long", "short"):
            errors.append(f'{tag}: kind must be "long" or "short"')
        if it.get("topic") not in TOPICS:
            errors.append(f"{tag}: topic must be one of {sorted(TOPICS)}")
        for k in ("title_en", "title_zh", "summary_en", "summary_zh", "url", "source"):
            if not it.get(k):
                errors.append(f"{tag}: missing {k}")
        if it.get("kind") == "long":
            words = len((it.get("summary_en") or "").split())
            if words < 120:
                warns.append(f"{tag}: long item has only {words} English words")
            if "\n\n" not in (it.get("summary_en") or ""):
                warns.append(f"{tag}: long item is a single paragraph")
    longs = sum(1 for it in d.get("items", []) if it.get("kind") == "long")
    shorts = len(d.get("items", [])) - longs
    if (longs, shorts) != (10, 10):
        warns.append(f"expected 10 long + 10 short, got {longs} + {shorts}")
    # ids already used on an earlier day
    for f in glob.glob(str(ROOT / "digests" / "*.json")):
        if Path(f).stem == date:
            continue
        old = {i["id"] for i in json.loads(Path(f).read_text())["items"]}
        for it in d.get("items", []):
            if it.get("id") in old:
                warns.append(f'{it["id"]}: already used in {Path(f).stem}')
    return errors, warns


def run(cmd, check=True, quiet=False):
    if not quiet:
        print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    out = (r.stdout + r.stderr).strip()
    if out and not quiet:
        print(out[-1500:])
    if check and r.returncode:
        sys.exit(f"command failed ({r.returncode}): {' '.join(cmd)}")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--wait", action="store_true", help="wait for the Pages deploy and check the live page")
    ap.add_argument("-m", "--message", default=None)
    a = ap.parse_args()

    path = ROOT / "digests" / f"{a.date}.json"
    if not path.exists():
        sys.exit(f"{path} does not exist. Write the digest file first.")
    try:
        d = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"{path.name} is not valid JSON: line {e.lineno} col {e.colno}: {e.msg}")

    cand = load_candidates()
    d = hydrate(d, cand)
    errors, warns = validate(d, a.date, cand)
    for w in warns:
        print("warning:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(f"{len(errors)} error(s); nothing was built or pushed.")
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    longs = [it for it in d["items"] if it["kind"] == "long"]
    print(f"digest ok: {len(longs)} long + {len(d['items']) - len(longs)} short, "
          f"{sum(1 for it in d['items'] if it.get('image'))} with image")

    run([sys.executable, "build.py"])
    if a.no_push:
        print("built only (--no-push). Preview: site/index.html")
        return

    run(["gh", "auth", "switch", "--user", GH_USER], check=False, quiet=True)
    run(["git", "add", "-A"])
    if run(["git", "diff", "--cached", "--quiet"], check=False, quiet=True).returncode == 0:
        print("nothing to commit")
    else:
        msg = (a.message or f"Digest for {a.date}") + "\n\n" + TRAILER
        run(["git", *GIT_ID, "commit", "-q", "-m", msg])
    run(["git", "pull", "-q", "--rebase", "origin", "main"])
    run(["git", "push", "-q", "origin", "main"])
    print("pushed. Live in about two minutes:", SITE_URL)

    if a.wait:
        import time, urllib.request
        time.sleep(15)
        r = run(["gh", "run", "list", "--repo", REPO, "--limit", "1", "--json", "databaseId", "--jq", ".[0].databaseId"], quiet=True)
        rid = r.stdout.strip()
        if rid:
            run(["gh", "run", "watch", rid, "--repo", REPO, "--exit-status", "--interval", "10"], check=False, quiet=True)
        for page in ("index.html", "index.zh.html"):
            html = urllib.request.urlopen(SITE_URL + page, timeout=20).read().decode("utf-8", "ignore")
            title = html.split("<title>")[1].split("<")[0] if "<title>" in html else "?"
            n_long = html.count('class="long"')
            n_short = html.count('class="short"')
            print(f"live {page}: {title} | long={n_long} short={n_short}")


if __name__ == "__main__":
    main()
