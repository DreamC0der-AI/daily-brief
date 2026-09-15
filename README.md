# Daily Brief

A personal, non-commercial daily reading digest covering tech, AI, crypto and bio, in English and Chinese.
Live at https://dreamc0der-ai.github.io/daily-brief/

## Purpose and use

- **Personal use only.** This site is built for one reader. It is not a news service, carries no advertising, sells nothing, and collects no visitor data.
- **Non-commercial.** No revenue is generated from this site in any form.
- **Attribution.** Every item links to its original source. Headlines and summaries are written in our own words from publicly available RSS feeds. Articles and images remain the property of their publishers; images are referenced from the publishers' own servers and are not copied or redistributed.
- **Takedown.** If you hold rights to any content shown here and want it removed, open an issue in this repository. It will be removed promptly, no questions asked.

## How it works

- `collect.py` fetches public RSS feeds listed in `feeds.json` once a day on GitHub Actions.
- A curated digest for each day is written by hand (with Claude Code) into `digests/`.
- `build.py` renders static HTML into `site/`, deployed to GitHub Pages.

See `CLAUDE.md` for the editing procedure.

## Disclaimer

The summaries are a reader's notes, provided as-is, and may contain errors. They are not advice of any kind. Always refer to the linked original article.
