# Daily Brief — personal news digest

Static daily news site (tech / AI / crypto / bio), English + Chinese, hosted on GitHub Pages.
No LLM API is used: **Claude Code, running in this folder, is the editor.**

## Layout
- `feeds.json` — RSS sources by topic (`name`, `url`, `lang`, `weight`). Add sources here.
- `collect.py` — fetches feeds → `data/candidates/YYYY-MM-DD.json` (deduped, last 36h, images resolved). Runs daily on GitHub Actions and commits the file.
- `digests/YYYY-MM-DD.json` — the curated digest written by Claude Code. If absent for a day, the site shows an "auto" page of top-scored items.
- `build.py` + `templates/page.html` — renders `site/` (index = latest day, one page per day, archive).
- `.github/workflows/daily.yml` — daily collect + build + deploy to Pages; also deploys on every push to main.
- `ddag.json` — DDAG claim graph for this project's design decisions.

Local setup: `uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt`. Run scripts with `.venv/bin/python`.

## Curation procedure (when the user says "make today's news" or similar)
1. `git pull`, then `.venv/bin/python collect.py` (fresh candidates; safe to rerun, overwrites today's file).
2. Read `data/candidates/<today>.json`. Skim all items (titles + excerpts). Do not fetch every article; open a page only when the excerpt is too thin to summarize honestly.
3. Pick **about 20 items**, roughly: AI 6–7, Tech 5–6, Crypto 3–4, Bio 3–4. Prefer: genuinely new developments over commentary, primary sources over rewrites, items with images when equal. Merge duplicates covering the same story into one item (link the best source). Skip press releases, listicles, deals/coupons.
4. Write `digests/<today>.json` following `digests/SCHEMA.md`. For each item write:
   - `title_en` / `title_zh`: a clear headline in each language (translate, do not transliterate; keep product names in Latin script).
   - `summary_en` / `summary_zh`: 2–3 sentences: what happened, why it matters. Written from the excerpt; no invented details or numbers.
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
