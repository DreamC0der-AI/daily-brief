#!/usr/bin/env python3
"""Render digests/*.json (curated) and data/candidates/*.json (auto fallback) into site/."""
import datetime as dt, html, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
TOPICS = {"ai": ("AI", "人工智能"), "tech": ("Tech", "科技"), "crypto": ("Crypto", "加密货币"), "bio": ("Bio", "生物医药")}
TEMPLATE = (ROOT / "templates" / "page.html").read_text()


def esc(s):
    return html.escape(s or "", quote=True)


def load_json(p):
    return json.loads(p.read_text())


def auto_digest(cand, n=20):
    """Uncurated fallback: top-scored items spread across topics."""
    by_topic = {}
    for it in cand["items"]:
        by_topic.setdefault(it["topic"], []).append(it)
    for v in by_topic.values():
        v.sort(key=lambda x: -x["score"])
    quota = {"ai": 6, "tech": 6, "crypto": 4, "bio": 4}
    picked = []
    for t, q in quota.items():
        picked += by_topic.get(t, [])[:q]
    items = []
    for it in picked[:n]:
        items.append({"id": it["id"], "kind": "short", "topic": it["topic"], "url": it["url"], "source": it["source"], "image": it["image"],
                      "title_en": it["title"] if it["lang"] == "en" else "", "title_zh": it["title"] if it["lang"] == "zh" else "",
                      "summary_en": it["excerpt"][:280] if it["lang"] == "en" else "", "summary_zh": it["excerpt"][:160] if it["lang"] == "zh" else ""})
    return {"date": cand["date"], "curated": False, "items": items,
            "intro_en": "Automatic pick of top feed items. No curated digest has been written for this day yet.",
            "intro_zh": "自动挑选的热门条目，本日尚未人工整理。"}


def paras(text, lang):
    return "".join(f'<p lang="{lang}">{esc(t.strip())}</p>' for t in (text or "").split("\n\n") if t.strip())


def bilingual(en, zh, tag="span"):
    en, zh = en or zh, zh or en
    return f'<{tag} lang="en">{esc(en)}</{tag}><{tag} lang="zh">{esc(zh)}</{tag}>'


def render_long(it, i):
    tag_en, tag_zh = TOPICS.get(it["topic"], (it["topic"], it["topic"]))
    img = f'<a class="hero" href="{esc(it["url"])}" target="_blank" rel="noopener"><img src="{esc(it["image"])}" alt="" loading="lazy" onerror="this.parentNode.remove()"></a>' if it.get("image") else ""
    why = f'<p class="why">{bilingual(it.get("why_en"), it.get("why_zh"))}</p>' if it.get("why_en") or it.get("why_zh") else ""
    return f'''<article class="long" id="{esc(it["id"])}">
  {img}
  <div class="meta"><span class="num">{i:02d}</span><span class="tag {esc(it["topic"])}"><span lang="en">{tag_en}</span><span lang="zh">{tag_zh}</span></span><span class="src">{esc(it["source"])}</span></div>
  <h2><a href="{esc(it["url"])}" target="_blank" rel="noopener">{bilingual(it.get("title_en"), it.get("title_zh"))}</a></h2>
  <div class="body">{paras(it.get("summary_en") or it.get("summary_zh"), "en")}{paras(it.get("summary_zh") or it.get("summary_en"), "zh")}</div>
  {why}
  <p class="more"><a href="{esc(it["url"])}" target="_blank" rel="noopener"><span lang="en">Read at {esc(it["source"])} &rarr;</span><span lang="zh">阅读原文（{esc(it["source"])}）&rarr;</span></a></p>
</article>'''


def render_short(it, i):
    tag_en, tag_zh = TOPICS.get(it["topic"], (it["topic"], it["topic"]))
    img = f'<a class="thumb" href="{esc(it["url"])}" target="_blank" rel="noopener"><img src="{esc(it["image"])}" alt="" loading="lazy" onerror="this.parentNode.remove()"></a>' if it.get("image") else ""
    return f'''<article class="short" id="{esc(it["id"])}">
  {img}
  <div class="sbody">
    <div class="meta"><span class="tag {esc(it["topic"])}"><span lang="en">{tag_en}</span><span lang="zh">{tag_zh}</span></span><span class="src">{esc(it["source"])}</span></div>
    <h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{bilingual(it.get("title_en"), it.get("title_zh"))}</a></h3>
    <p class="sum">{bilingual(it.get("summary_en"), it.get("summary_zh"))}</p>
  </div>
</article>'''


def render_page(d, dates, curated):
    items = d["items"]
    longs = [it for it in items if it.get("kind") == "long"]
    shorts = [it for it in items if it.get("kind") != "long"]
    sections = []
    if longs:
        sections.append(f'<section id="depth"><h3 class="topic"><span lang="en">In depth</span><span lang="zh">深度</span><small>{len(longs)}</small></h3>' +
                        "".join(render_long(it, i) for i, it in enumerate(longs, 1)) + "</section>")
    if shorts:
        sections.append(f'<section id="briefs"><h3 class="topic"><span lang="en">Briefs</span><span lang="zh">简讯</span><small>{len(shorts)}</small></h3><div class="shorts">' +
                        "".join(render_short(it, i) for i, it in enumerate(shorts, 1)) + "</div></section>")
    idx = dates.index(d["date"])
    prev = f'<a href="{dates[idx+1]}.html">&larr; {dates[idx+1]}</a>' if idx + 1 < len(dates) else "<span></span>"
    nxt = f'<a href="{dates[idx-1]}.html">{dates[idx-1]} &rarr;</a>' if idx > 0 else "<span></span>"
    day = dt.date.fromisoformat(d["date"])
    badge = '<span class="badge ok"><span lang="en">curated</span><span lang="zh">人工整理</span></span>' if curated else '<span class="badge auto"><span lang="en">auto</span><span lang="zh">自动</span></span>'
    return (TEMPLATE
            .replace("{{DATE}}", d["date"])
            .replace("{{DATE_LONG_EN}}", day.strftime("%A, %B %-d, %Y"))
            .replace("{{DATE_LONG_ZH}}", f"{day.year}年{day.month}月{day.day}日 " + "周一周二周三周四周五周六周日"[day.weekday()*2:day.weekday()*2+2])
            .replace("{{BADGE}}", badge)
            .replace("{{INTRO_EN}}", esc(d.get("intro_en", "")))
            .replace("{{INTRO_ZH}}", esc(d.get("intro_zh", "")))
            .replace("{{COUNT}}", str(len(items)))
            .replace("{{SECTIONS}}", "\n".join(sections))
            .replace("{{PREV}}", prev).replace("{{NEXT}}", nxt))


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    curated = {p.stem: load_json(p) for p in (ROOT / "digests").glob("*.json")}
    cands = {p.stem: p for p in (ROOT / "data" / "candidates").glob("*.json")}
    dates = sorted(set(curated) | set(cands), reverse=True)
    if not dates:
        raise SystemExit("nothing to build")
    for date in dates:
        if date in curated:
            d, is_cur = curated[date], True
        else:
            d, is_cur = auto_digest(load_json(cands[date])), False
        page = render_page(d, dates, is_cur)
        (SITE / f"{date}.html").write_text(page)
        if date == dates[0]:
            (SITE / "index.html").write_text(page)
    rows = "".join(f'<li><a href="{d}.html">{d}</a> {"<span class=badge-sm>curated</span>" if d in curated else ""}</li>' for d in dates)
    archive = TEMPLATE.replace("{{SECTIONS}}", f'<ul class="archive">{rows}</ul>').replace("{{DATE}}", "Archive") \
        .replace("{{DATE_LONG_EN}}", "Archive").replace("{{DATE_LONG_ZH}}", "往期").replace("{{BADGE}}", "") \
        .replace("{{INTRO_EN}}", "").replace("{{INTRO_ZH}}", "").replace("{{COUNT}}", str(len(dates))) \
        .replace("{{PREV}}", "").replace("{{NEXT}}", "")
    (SITE / "archive.html").write_text(archive)
    (SITE / ".nojekyll").write_text("")
    for f in (ROOT / "static").glob("*"):
        shutil.copy(f, SITE / f.name)
    print(f"built {len(dates)} day(s) -> site/  latest={dates[0]} curated={dates[0] in curated}")


if __name__ == "__main__":
    main()
