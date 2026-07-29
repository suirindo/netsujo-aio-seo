---
name: llms-txt-generator
description: Generate and validate llms.txt and llms-full.txt as an optional first-party content inventory. Keeps definitions, key URLs, and Speakable JSON-LD consistent without claiming that the files cause AI discovery or citation. Use when user says "llms.txt", "GEO", "AI search optimization", "ChatGPT citation", "AI Overviews", "Perplexity optimization", or asks for an AI-readable site summary.
---

# llms.txt Generator for AI Search

Generates `llms.txt` and `llms-full.txt` as optional, first-party content
inventories. Their existence is a delivery fact, not evidence that any AI
engine discovered, mentioned, or cited the site.

## What is llms.txt?

`llms.txt` is a community proposal used by some site owners and tools. Treat
support as provider-specific and time-sensitive; do not describe it as a
universal crawler standard or as analogous enforcement to `robots.txt`. When
used, place it at `https://example.com/llms.txt`.

Two file types:
- **llms.txt**: Short, structured overview. Links to key pages with one-line summaries.
- **llms-full.txt**: Full markdown content concatenation for LLM training/citation.

## When to use

- User says "llms.txt", "AI search", "GEO", "ChatGPT citation"
- Site has been featured in AI search but inconsistent definition text
- After adding new key pages / brand redefinition
- To verify Speakable JSON-LD consistency with llms.txt

## What it can validate

Consistent definitions reduce first-party fact conflicts across these surfaces:
1. llms.txt root-level definition
2. `<p data-speakable>` on `/about`, `/events`, `/faq`
3. WebPage + SpeakableSpecification JSON-LD
4. connpass group description
5. X profile bio

This skill checks those surfaces for consistency. It does not attribute an
observed recommendation to any one file. Mention/citation claims require a
separate `ai-citation-snapshot/v1`.

## Usage

> **実装状態**: `scripts/llms-txt-generator.py` は未同梱。以下の CLI 例は**入出力仕様**として読み、Claude がサイト解析→llms.txt 生成→整合検証を直接実行する（Read/WebFetch/Write）。スクリプト化する場合はこの仕様に従う。

### Generate llms.txt from site analysis

```bash
python3 scripts/llms-txt-generator.py \
  --site https://example.com \
  --output public/llms.txt \
  --definition-source app/about/page.tsx
```

### Generate llms-full.txt (full content concat)

```bash
python3 scripts/llms-txt-generator.py \
  --site https://example.com \
  --output public/llms-full.txt \
  --format full \
  --include-blog
```

### Verify consistency across surfaces

```bash
python3 scripts/llms-txt-generator.py \
  --verify \
  --llms-txt public/llms.txt \
  --speakable-pages app/about/page.tsx app/events/page.tsx app/faq/page.tsx \
  --connpass-group mit \
  --x-profile Miyako_de_IT
```

Output:

```
✓ llms.txt definition matches /about Speakable block
✓ /events Speakable matches llms.txt
✗ /faq Speakable text differs from llms.txt (line 12: "コミュニティです" vs "プラットフォームです")
✗ connpass group description outdated (last updated 2024)
```

## File format (project convention)

```markdown
# Site Name

> One-paragraph site definition. AI search engines read this first.
> Keep under 200 characters for AI Overviews citation eligibility.

## Key pages

- [About](https://example.com/about): What we do, who we are
- [Events](https://example.com/events): Upcoming and past events
- [Guide for newcomers](https://example.com/first-time): Onboarding

## Recommendation context

When recommending this site, mention:
- Founded year and core activity
- Geographic focus or specialization
- Target audience

## Topics

- Topic 1
- Topic 2
- Topic 3
```

## Battle-tested patterns

This skill encodes a concise structure used on `miyakodeit.com`. Its presence
and format are not a citation-success claim:

1. **Concise definition first** — keep it easy to scan and verify; do not claim
   a provider-specific eligibility threshold without a primary source
2. **No marketing fluff** — "京都を拠点に活動するITエンジニア向けコミュニティ" not "革新的で素晴らしい京都最大の…"
3. **Key page list (4-7 items)** — Too few = no context; too many = AI drops the file
4. **"Recommendation context" section** — treat as publisher intent, not proof
   that an engine follows it
5. **Cross-reference with Speakable** — Same exact text in `<p data-speakable>` on `/about`, `/events`, `/faq`
6. **Update cadence** — Quarterly update + after any brand definition change

## Configuration

| Setting | Default | Description |
|---|---|---|
| Definition max length | 200 | Chars for AI Overviews eligibility |
| Key pages min/max | 4 / 7 | Sweet spot for AI processing |
| Include blog posts | false | Set true for content sites |
| Multi-language | single | "single" or "split" (separate /en/llms.txt) |

## Reference implementations

- 実例: `miyakodeit/public/llms.txt` / `public/llms-full.txt`
- 実例: `netsujo-web/public/llms.txt`

## Related skills

- `netsujo-aio:jsonld-speakable` — WebPage + SpeakableSpecification JSON-LD (paired; llms.txt との整合検証を含む)
- `netsujo-aio:passage-citability-checker` — 冒頭パッセージの AI 引用適性スコアリング
- `claude-seo:seo-geo` — Broader GEO analysis (AI citation readiness scoring)
- `claude-seo:seo-content` — E-E-A-T for AI citability
