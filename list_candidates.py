#!/usr/bin/env python3
"""Write a compact, skimmable list of today's candidates to data/fetched/DATE.list.txt (gitignored).

Usage: .venv/bin/python list_candidates.py [--date YYYY-MM-DD]
Each line: flag, id, source, image?, published, title.   Flag H = hot (Hacker News >= 300 points).
Items already used in any earlier digest are left out. Hot items are repeated in a block at the top.
Only counts are printed; read the output file for the list.
"""
import argparse, datetime as dt, glob, json
from pathlib import Path

ROOT = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    d = json.loads((ROOT / "data" / "candidates" / f"{a.date}.json").read_text())
    used = set()
    for f in glob.glob(str(ROOT / "digests" / "*.json")):
        if Path(f).stem != a.date:
            used |= {i["id"] for i in json.loads(Path(f).read_text())["items"]}
    items = [i for i in d["items"] if i["id"] not in used]

    def line(it):
        pts = f" [{it['points']} pts]" if it.get("points") else ""
        return (f"{'H' if it.get('hot') else ' '} {it['id']} {it['source'][:14]:14} {'I' if it.get('image') else '-'} "
                f"{it['published'][5:16]} {it['title'][:110]}{pts}")

    feed_errors = ", ".join(d.get("errors") or []) or "none"
    total = len(d["items"])
    out = [f"# candidates {a.date}: {len(items)} unused of {total}; feed errors: {feed_errors}", "",
           "== HOT (check these first) =="]
    out += [line(i) for i in sorted(items, key=lambda x: -(x.get("points") or 0)) if i.get("hot")]
    for t in ("ai", "tech", "crypto", "bio"):
        out += ["", f"== {t.upper()} =="]
        out += [line(i) for i in sorted((i for i in items if i["topic"] == t), key=lambda x: -x["score"])]
    path = ROOT / "data" / "fetched" / f"{a.date}.list.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n")
    print(f"{len(items)} unused candidates, {sum(1 for i in items if i.get('hot'))} hot -> {path}")


if __name__ == "__main__":
    main()
