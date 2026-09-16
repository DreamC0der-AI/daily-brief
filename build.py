#!/usr/bin/env python3
"""Render digests/*.json (curated) and data/candidates/*.json (auto fallback) into site/.

Each day produces two pages: YYYY-MM-DD.html (English) and YYYY-MM-DD.zh.html (Chinese),
each with its own Open Graph tags and preview card so shared links show the right language.
"""
import datetime as dt, html, json, shutil
from pathlib import Path
import og

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BASE_URL = "https://dreamc0der-ai.github.io/daily-brief/"
TOPICS = {"ai": ("AI", "人工智能"), "tech": ("Tech", "科技"), "crypto": ("Crypto", "加密货币"), "bio": ("Bio", "生物医药")}
TEMPLATE = (ROOT / "templates" / "page.html").read_text()
T = {  # UI strings
    "en": dict(archive="Archive", share="Share", indepth="In depth", briefs="Briefs", items="items", curated="curated", auto="auto",
               readat="Read at {src} →", share_page="Share today's brief", share_item="Share this story", wechat="WeChat", wechat_hint="Scan in WeChat, or copy the link and paste it into a chat",
               copy="Copy link", copied="Copied", copytext="Copy text", native="More…", other_lang="中文", intro_auto="Automatic pick of top feed items. No curated digest has been written for this day yet.",
               site_title="Daily Brief", desc_suffix=""),
    "zh": dict(archive="往期", share="分享", indepth="深度", briefs="简讯", items="条", curated="人工整理", auto="自动",
               readat="阅读原文（{src}）→", share_page="分享今日简报", share_item="分享这条新闻", wechat="微信", wechat_hint="用微信扫一扫，或复制链接后粘贴到聊天中",
               copy="复制链接", copied="已复制", copytext="复制文字", native="更多…", other_lang="EN", intro_auto="自动挑选的热门条目，本日尚未人工整理。",
               site_title="Daily Brief 每日简报", desc_suffix=""),
}


def esc(s):
    return html.escape(s or "", quote=True)


def load_json(p):
    return json.loads(p.read_text())


def pick(it, key, lang):
    return it.get(f"{key}_{lang}") or it.get(f"{key}_{'en' if lang == 'zh' else 'zh'}") or ""


def auto_digest(cand, n=20):
    by_topic = {}
    for it in cand["items"]:
        by_topic.setdefault(it["topic"], []).append(it)
    for v in by_topic.values():
        v.sort(key=lambda x: -x["score"])
    picked = []
    for t, q in {"ai": 6, "tech": 6, "crypto": 4, "bio": 4}.items():
        picked += by_topic.get(t, [])[:q]
    items = [{"id": it["id"], "kind": "short", "topic": it["topic"], "url": it["url"], "source": it["source"], "image": it["image"],
              "title_en": it["title"] if it["lang"] == "en" else "", "title_zh": it["title"] if it["lang"] == "zh" else "",
              "summary_en": it["excerpt"][:280] if it["lang"] == "en" else "", "summary_zh": it["excerpt"][:160] if it["lang"] == "zh" else ""}
             for it in picked[:n]]
    return {"date": cand["date"], "items": items, "intro_en": T["en"]["intro_auto"], "intro_zh": T["zh"]["intro_auto"]}


def page_name(date, lang):
    return f"{date}.html" if lang == "en" else f"{date}.zh.html"


def date_label(day, lang):
    if lang == "en":
        return day.strftime("%A, %B %-d, %Y")
    return f"{day.year}年{day.month}月{day.day}日 " + "周一周二周三周四周五周六周日"[day.weekday()*2:day.weekday()*2+2]


def share_attrs(title, url):
    return f'data-share-title="{esc(title)}" data-share-url="{esc(url)}"'


def render_long(it, i, lang, page_url):
    s = T[lang]
    tag = TOPICS.get(it["topic"], (it["topic"], it["topic"]))[0 if lang == "en" else 1]
    title = pick(it, "title", lang)
    item_url = f"{page_url}#{it['id']}"
    img = f'<a class="hero" href="{esc(it["url"])}" target="_blank" rel="noopener"><img src="{esc(it["image"])}" alt="" loading="lazy" onerror="this.parentNode.remove()"></a>' if it.get("image") else ""
    body = "".join(f"<p>{esc(p.strip())}</p>" for p in pick(it, "summary", lang).split("\n\n") if p.strip())
    why = f'<p class="why">{esc(pick(it, "why", lang))}</p>' if it.get("why_en") or it.get("why_zh") else ""
    return f'''<article class="long" id="{esc(it["id"])}">
  {img}
  <div class="meta"><span class="num">{i:02d}</span><span class="tag {esc(it["topic"])}">{tag}</span><span class="src">{esc(it["source"])}</span>
    <button class="share-btn small" {share_attrs(title, item_url)} data-share-qr="{esc(it['id'])}" aria-label="{s['share_item']}">{ICON_SHARE}</button></div>
  <h2><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(title)}</a></h2>
  <div class="body">{body}</div>
  {why}
  <p class="more"><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(s["readat"].format(src=it["source"]))}</a></p>
  <template id="qr-{esc(it['id'])}">{og.qr_svg(item_url)}</template>
</article>'''


def render_short(it, lang):
    tag = TOPICS.get(it["topic"], (it["topic"], it["topic"]))[0 if lang == "en" else 1]
    img = f'<a class="thumb" href="{esc(it["url"])}" target="_blank" rel="noopener"><img src="{esc(it["image"])}" alt="" loading="lazy" onerror="this.parentNode.remove()"></a>' if it.get("image") else ""
    return f'''<article class="short" id="{esc(it["id"])}">
  {img}
  <div class="sbody">
    <div class="meta"><span class="tag {esc(it["topic"])}">{tag}</span><span class="src">{esc(it["source"])}</span></div>
    <h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(pick(it, "title", lang))}</a></h3>
    <p class="sum">{esc(pick(it, "summary", lang))}</p>
  </div>
</article>'''


ICON_SHARE = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M16 6l-4-4-4 4"/><path d="M12 2v13"/></svg>'


def render_page(d, dates, curated, lang):
    s = T[lang]
    date = d["date"]
    page_url = BASE_URL + page_name(date, lang)
    items = d["items"]
    longs = [it for it in items if it.get("kind") == "long"]
    shorts = [it for it in items if it.get("kind") != "long"]
    sections = []
    if longs:
        sections.append(f'<section id="depth"><h3 class="topic">{s["indepth"]}<small>{len(longs)}</small></h3>' +
                        "".join(render_long(it, i, lang, page_url) for i, it in enumerate(longs, 1)) + "</section>")
    if shorts:
        sections.append(f'<section id="briefs"><h3 class="topic">{s["briefs"]}<small>{len(shorts)}</small></h3><div class="shorts">' +
                        "".join(render_short(it, lang) for it in shorts) + "</div></section>")
    idx = dates.index(date)
    prev = f'<a href="{page_name(dates[idx+1], lang)}">&larr; {dates[idx+1]}</a>' if idx + 1 < len(dates) else "<span></span>"
    nxt = f'<a href="{page_name(dates[idx-1], lang)}">{dates[idx-1]} &rarr;</a>' if idx > 0 else "<span></span>"
    day = dt.date.fromisoformat(date)
    label = date_label(day, lang)
    badge = f'<span class="badge {"ok" if curated else "auto"}">{s["curated"] if curated else s["auto"]}</span>'
    intro = pick(d, "intro", lang)
    headlines = [pick(it, "title", lang) for it in (longs or shorts)[:3]]
    share_title = f"{s['site_title']} · {label}"
    share_text = share_title + "\n\n" + "\n".join(f"{i}. {h}" for i, h in enumerate(headlines, 1))
    og_img = f"og/{date}.{lang}.png"
    desc = intro if len(intro) < 200 else intro[:197] + "…"
    other = page_name(date, "zh" if lang == "en" else "en")
    repl = {
        "{{LANG}}": "zh-CN" if lang == "zh" else "en", "{{LANGCODE}}": lang, "{{TITLE}}": esc(share_title),
        "{{DESC}}": esc(desc), "{{URL}}": esc(page_url), "{{OG_IMAGE}}": esc(BASE_URL + og_img), "{{OTHER_URL}}": esc(other),
        "{{OTHER_LANG}}": s["other_lang"], "{{ARCHIVE}}": s["archive"], "{{SHARE}}": s["share"], "{{DATE}}": date,
        "{{DATE_LONG}}": esc(label), "{{BADGE}}": badge, "{{COUNT}}": str(len(items)), "{{ITEMS_WORD}}": s["items"],
        "{{INTRO}}": esc(intro), "{{INDEPTH}}": s["indepth"], "{{BRIEFS}}": s["briefs"], "{{SECTIONS}}": "\n".join(sections),
        "{{PREV}}": prev, "{{NEXT}}": nxt, "{{SHARE_TITLE}}": esc(share_title), "{{SHARE_TEXT}}": esc(share_text),
        "{{SHARE_PAGE}}": s["share_page"], "{{SHARE_ITEM}}": s["share_item"], "{{WECHAT}}": s["wechat"], "{{WECHAT_HINT}}": s["wechat_hint"],
        "{{COPY}}": s["copy"], "{{COPIED}}": s["copied"], "{{COPYTEXT}}": s["copytext"], "{{NATIVE}}": s["native"],
        "{{PAGE_QR}}": og.qr_svg(page_url), "{{ICON}}": ICON_SHARE, "{{INDEX_HREF}}": "index.html" if lang == "en" else "index.zh.html",
    }
    out = TEMPLATE
    for k, v in repl.items():
        out = out.replace(k, v)
    return out, (label, headlines, og_img)


def render_archive(dates, curated):
    rows = "".join(f'<li><span class="d">{d}</span> <a href="{page_name(d, "en")}">English</a> · <a href="{page_name(d, "zh")}">中文</a>'
                   f'{" <span class=badge-sm>curated</span>" if d in curated else ""}</li>' for d in dates)
    out, _ = render_page({"date": dates[0], "items": [], "intro_en": "", "intro_zh": ""}, dates, True, "en")
    # crude but effective: swap the body of the latest page for the archive list
    out = out.replace('<section id="depth">', "").replace("</section>", "")
    start, end = out.index('<h1 class="date">'), out.index('<div class="pager">')
    return out[:start] + f'<h1 class="date">Archive · 往期</h1><ul class="archive">{rows}</ul>' + out[end:]


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "og").mkdir(parents=True)
    curated = {p.stem: load_json(p) for p in (ROOT / "digests").glob("*.json")}
    cands = {p.stem: p for p in (ROOT / "data" / "candidates").glob("*.json")}
    dates = sorted(set(curated) | set(cands), reverse=True)
    if not dates:
        raise SystemExit("nothing to build")
    for date in dates:
        d, is_cur = (curated[date], True) if date in curated else (auto_digest(load_json(cands[date])), False)
        for lang in ("en", "zh"):
            page, (label, headlines, og_img) = render_page(d, dates, is_cur, lang)
            (SITE / page_name(date, lang)).write_text(page)
            og.card(label, headlines, lang, SITE / og_img)
            if date == dates[0]:
                # index pages: same content, plus a one-time language redirect on the English landing page
                idx = page
                if lang == "en":
                    idx = idx.replace("<!--INDEX_REDIRECT-->", '<script>try{var l=localStorage.getItem("dailybrief-lang")||((navigator.language||"").startsWith("zh")?"zh":"en");if(l==="zh"&&!location.hash)location.replace("index.zh.html")}catch(e){}</script>')
                (SITE / ("index.html" if lang == "en" else "index.zh.html")).write_text(idx)
    (SITE / "archive.html").write_text(render_archive(dates, curated))
    (SITE / ".nojekyll").write_text("")
    for f in (ROOT / "static").glob("*"):
        shutil.copy(f, SITE / f.name)
    print(f"built {len(dates)} day(s) x 2 languages -> site/  latest={dates[0]} curated={dates[0] in curated}")


if __name__ == "__main__":
    main()
