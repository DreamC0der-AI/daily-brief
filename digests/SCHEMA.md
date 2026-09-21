# Digest file schema — digests/YYYY-MM-DD.json

Written by the editor with the file-writing tool, as plain data. Never generate it by running code.
`publish.py` validates it, fills in missing fields from the candidates files, and normalizes it.

```json
{
  "date": "2026-09-21",
  "intro_en": "One or two sentences on the day's themes.",
  "intro_zh": "一两句话概括今天的主题。",
  "items": [
    {
      "id": "a1b2c3d4e5",
      "kind": "long",
      "topic": "ai",
      "title_en": "...",
      "title_zh": "...",
      "summary_en": ["Paragraph one.", "Paragraph two.", "Paragraph three."],
      "summary_zh": ["第一段。", "第二段。", "第三段。"],
      "why_en": "optional one-line editor note",
      "why_zh": "可选的一句编辑按语"
    },
    {
      "id": "f6e5d4c3b2",
      "kind": "short",
      "topic": "crypto",
      "title_en": "...",
      "title_zh": "...",
      "summary_en": "One or two sentences.",
      "summary_zh": "一两句话。"
    }
  ]
}
```

Fields
- `id` (required): the candidate id. `url`, `source`, `image` and `topic` are filled in from the candidates files when omitted. Give them explicitly only to override (for example a better `source` label or `"image": null`).
- `kind`: `long` (in-depth, about three paragraphs) or `short` (one or two sentences). Aim for 10 + 10.
- `topic`: `ai` | `tech` | `crypto` | `bio`.
- `summary_en` / `summary_zh`: a string, or a list of paragraphs (preferred for long items). After `publish.py` runs, lists are stored as one string with blank lines between paragraphs.

Writing rules that keep the JSON valid
- Use typographic quotes “like this” inside English text, never straight double quotes. Apostrophes are fine.
- No raw line breaks inside a string; use the paragraph list instead.

Items render in two sections, "In depth" (long) then "Briefs" (short), each in file order, most important first. The first long item with an image supplies the share thumbnail.
