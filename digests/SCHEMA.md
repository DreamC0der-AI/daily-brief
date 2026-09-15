# Digest file schema — digests/YYYY-MM-DD.json

```json
{
  "date": "2026-09-15",
  "intro_en": "One or two sentences on the day's themes.",
  "intro_zh": "一两句话概括今天的主题。",
  "items": [
    {
      "id": "a1b2c3d4e5",            // from candidates
      "topic": "ai",                  // ai | tech | crypto | bio
      "source": "The Verge",          // from candidates
      "url": "https://...",           // from candidates
      "image": "https://... or null", // from candidates (may be swapped for a better one)
      "title_en": "...",
      "title_zh": "...",
      "summary_en": "2–3 sentences.",
      "summary_zh": "两三句话。",
      "why_en": "optional one-line editor note",
      "why_zh": "可选的一句编辑按语"
    }
  ]
}
```
Items are rendered grouped by topic in the order ai, tech, crypto, bio; within a topic in file order (put the most important first).
