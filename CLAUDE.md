# Daily Brief — personal news digest

Static daily news site (tech / AI / crypto / bio), English + Chinese, hosted on GitHub Pages.
No LLM API is used: **Claude Code, running in this folder, is the editor.**

## Layout
- `feeds.json` — RSS sources by topic (`name`, `url`, `lang`, `weight`). Add sources here.
- `collect.py` — fetches feeds → `data/candidates/YYYY-MM-DD.json` (deduped, last 36h, images resolved). Runs daily on GitHub Actions and commits the file.
- `digests/YYYY-MM-DD.json` — the curated digest written by Claude Code. If absent for a day, the site shows an "auto" page of top-scored items.
- `build.py` + `templates/page.html` — renders `site/`: two pages per day (`DATE.html` English, `DATE.zh.html` Chinese) each with its own Open Graph tags, `index.html` / `index.zh.html`, and `archive.html`. `og.py` draws the 1200x630 preview card per day per language (`site/og/`) and the inline QR codes for the WeChat share. Share dialog (WeChat QR + copy, X, Telegram, WhatsApp, Weibo, copy, native share) is in the template; per-language pages exist so shared links preview in the right language.
- `.github/workflows/daily.yml` — daily collect + build + deploy to Pages; also deploys on every push to main.
- `ddag.json` — DDAG claim graph for this project's design decisions.

Local setup: `uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt`. Run scripts with `.venv/bin/python`.

## Curation procedure (when the user says "make today's news" or similar)
1. `git pull`, then `.venv/bin/python collect.py` (fresh candidates; safe to rerun, overwrites today's file).
2. Read `data/candidates/<today>.json`. Skim all items (titles + excerpts). Do not fetch every article; open a page only when the excerpt is too thin to summarize honestly.
3. Pick **20 items in two tiers** (user's rule, set 2026-09-15):
   - **10 in-depth** (`kind: "long"`): the stories that matter most today. Fetch the article text for every one of these (plain HTTP with a browser User-Agent works for most; The Block, BioPharma Dive and Science block it, so lean on sibling coverage). Write 3 paragraphs, roughly 150–220 English words / 300–450 Chinese characters: what happened, the substance and numbers, and context or reaction. Separate paragraphs with a blank line (`\n\n`).
   - **10 briefs** (`kind: "short"`): 1–2 sentences each, written from the excerpt.
   - Mix across topics; a typical day is AI 6–7, Tech 5–6, Crypto 3–4, Bio 3–4 in total. Prefer genuinely new developments over commentary, primary sources over rewrites, items with images when equal. Merge duplicates covering the same story into one item (link the best source). Skip press releases, listicles, deals/coupons.
4. Write `digests/<today>.json` following `digests/SCHEMA.md`. For each item write:
   - `title_en` / `title_zh`: a clear headline in each language (translate, do not transliterate; keep product names in Latin script).
   - `summary_en` / `summary_zh`: per the tier above. No invented details or numbers; if a number is not in the source, leave it out.
   - `why_en` / `why_zh` (optional, one line): the editor's note on significance or context.
   - Copy `id`, `url`, `source`, `image`, `topic` verbatim from the candidate.
   - `intro_en` / `intro_zh`: 1–2 sentence overview of the day's themes.
5. `.venv/bin/python build.py` and open `site/index.html` to sanity-check (both languages, images load).
6. Commit `digests/<today>.json` (and `data/candidates/<today>.json`) and push to main. Actions deploys within ~2 minutes.

## Rules
- Never fabricate facts. Summaries come from the candidate excerpt or the article itself.
- Chinese summaries are written natively in Simplified Chinese, not machine-literal translations.
- Keep to the user's stated volume (~20 items). Quality over coverage.
- When adding a feed, probe it first (200, entries > 0, dates parse) before adding to `feeds.json`.
