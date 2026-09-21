# Daily Brief — personal news digest

Static daily news site (tech / AI / crypto / bio), English + Chinese, hosted on GitHub Pages.
No LLM API is used: **Claude Code, running in this folder, is the editor.**

## Layout
- `feeds.json` — RSS sources by topic (`name`, `url`, `lang`, `weight`). Add sources here.
- `collect.py` — fetches feeds → `data/candidates/YYYY-MM-DD.json` (deduped, last 36h, images resolved). Runs daily on GitHub Actions and commits the file. Hacker News items with 300+ points are flagged `hot`, kept for 72h, scored higher and listed in the run output.
- `list_candidates.py` — writes a compact skimmable list of the day's unused candidates (hot block first) to `data/fetched/DATE.list.txt`.
- `fetch.py` — fetches article text for given candidate ids into `data/fetched/DATE.txt`.
- `digests/YYYY-MM-DD.json` — the curated digest, written by Claude Code as a plain data file (see `digests/SCHEMA.md`). If absent for a day, the site shows an "auto" page of top-scored items, which is mostly English on both language pages because feed items carry only their original language.
- `publish.py` — validates the digest, fills url/source/image/topic from candidates, builds the site, commits and pushes.
- `build.py` + `templates/page.html` — renders `site/`: two pages per day (`DATE.html` English, `DATE.zh.html` Chinese) each with its own Open Graph tags, `index.html` / `index.zh.html`, and `archive.html`. `og.py` makes the preview images per day per language in `site/og/`: the lead story's photo cropped to 1200x630 (og:image) and 400x400 (hidden first image, which WeChat uses for its card thumbnail); if the photo cannot be fetched it falls back to a generated headline card. It also makes the inline QR codes for the WeChat share. Share dialog (WeChat QR + copy, X, Telegram, WhatsApp, Weibo, copy, native share) is in the template; per-language pages exist so shared links preview in the right language.
- `.github/workflows/daily.yml` — daily collect + build + deploy to Pages; also deploys on every push to main.
- `.claude/settings.json` — allowlist for the fixed commands below, so they run without prompts.
- `data/fetched/` — scratch output of `list_candidates.py` and `fetch.py`; gitignored.
- `ddag.json` — DDAG claim graph for this project's design decisions.

Local setup: `uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt`.

## Curation procedure (when the user says "make today's news" or similar)

Use ONLY these fixed commands, run from the project root exactly as written (no `cd … &&` prefix, no inline Python, no heredocs). They are allowlisted. Anything that varies from day to day goes into a file written with the Write tool, never into a shell command.

1. `git pull`
2. `.venv/bin/python collect.py` — on Mondays, or after skipped days, add `--hours 72`.
3. `.venv/bin/python list_candidates.py` then Read `data/fetched/<today>.list.txt`. Look at the HOT block first; a hot item is a story the community already decided matters.
4. Pick **20 items in two tiers** (user's rule, set 2026-09-15):
   - **10 in-depth** (`kind: "long"`): the stories that matter most. Three paragraphs, roughly 150–250 English words / 300–600 Chinese characters: what happened, the substance and numbers, context or reaction.
   - **10 briefs** (`kind: "short"`): 1–2 sentences each.
   - Mix across topics; a typical day is AI 6–8, Tech 5–6, Crypto 3–4, Bio 3–4. Prefer genuinely new developments over commentary, primary sources over rewrites, items with images when equal. Merge duplicates covering one story into one item (link the best source, cite the others in the text). Skip press releases, listicles, deals.
   - The user's priority is the **latest developments in the AI industry**: new models, labs, launches, incidents. Do not let a launch slip because its title is opaque; open it.
5. `.venv/bin/python fetch.py ID ID …` for every in-depth pick and its sibling sources, plus any brief whose excerpt is thin. Read `data/fetched/<today>.txt`. The Block, BioPharma Dive, Science, Fierce Biotech and some lab blogs return no text; lean on sibling coverage or the excerpt. Use `--append` for a second round.
6. Write `digests/<today>.json` with the Write tool, following `digests/SCHEMA.md`: only `id`, `kind`, `topic`, titles, summaries, optional `why_*`, plus `intro_en` / `intro_zh`. Paragraphs as a list. Typographic quotes “ ” in English text, never straight double quotes.
7. `.venv/bin/python publish.py --wait` — validates, builds, commits, pushes, waits for the deploy and prints the live page counts. If it reports errors, fix the JSON and rerun. Use `--no-push` for a local preview, `--date` for another day.

If a shell command is blocked by the permission system, do not work around it with a differently shaped command. Tell the user; the digest file is already on disk and `publish.py` is all that remains.

## Rules
- Never fabricate facts. Summaries come from the fetched article text or the candidate excerpt. If a number is not in the source, leave it out.
- Chinese summaries are written natively in Simplified Chinese, not machine-literal translations. Keep product and model names in Latin script.
- Keep to the user's stated volume (10 + 10). Quality over coverage.
- When adding a feed, probe it first (200, entries > 0, dates parse) before adding to `feeds.json`. Most AI lab blogs (Anthropic, Meta, Mistral, xAI, Z.ai, TypeSafe) have no RSS; rely on Hacker News Best, The Decoder, Latent Space and the Chinese outlets for launches.
- The Chinese "curated" badge reads "AI 精选": the editor is an AI, do not describe the work as 人工.
- `gh` sometimes reverts its active account; `publish.py` switches to DreamC0der-AI before pushing.
