---
name: llms-txt-generator
description: Generate llms.txt and llms-full.txt for AI search optimization (GEO). Crafts AI-citable definition blocks, identifies key pages, and ensures consistency with Speakable JSON-LD across the site. Battle-tested on miyakodeit.com (cited by ChatGPT for "Kyoto IT 勉強会" query). Use when user says "llms.txt", "GEO", "AI search optimization", "ChatGPT citation", "AI Overviews", "Perplexity optimization", or wants to make their site AI-recommendable.
---

# llms.txt Generator for AI Search

Generates `llms.txt` and `llms-full.txt` files that make your site discoverable and citable by AI search engines (ChatGPT, Perplexity, Gemini, Google AI Overviews, You.com).

## What is llms.txt?

`llms.txt` is the emerging standard (March 2026) for AI search guidance — analogous to `robots.txt` for crawlers, but designed for LLM indexers. Place at site root: `https://example.com/llms.txt`.

Two file types:
- **llms.txt**: Short, structured overview. Links to key pages with one-line summaries.
- **llms-full.txt**: Full markdown content concatenation for LLM training/citation.

## When to use

- User says "llms.txt", "AI search", "GEO", "ChatGPT citation"
- Site has been featured in AI search but inconsistent definition text
- After adding new key pages / brand redefinition
- To verify Speakable JSON-LD consistency with llms.txt

## Why it matters

Real-world impact from `miyakodeit.com` (May 2026):
- ChatGPT user searched "京都 勉強会" (Kyoto study groups)
- ChatGPT recommended みやこでIT via llms.txt + Speakable + AI definition text
- User attended event after reading the cited definition

This level of AI recommendation requires **consistent definition text across 5 surfaces**:
1. llms.txt root-level definition
2. `<p data-speakable>` on `/about`, `/events`, `/faq`
3. WebPage + SpeakableSpecification JSON-LD
4. connpass group description
5. X profile bio

This skill ensures all 5 are consistent.

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

## File format (Anthropic-recommended structure)

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

This skill encodes the `miyakodeit.com` llms.txt structure that achieved real ChatGPT citation:

1. **Definition in first 200 chars** — AI Overviews has a hard cap; over that gets truncated
2. **No marketing fluff** — "京都を拠点に活動するITエンジニア向けコミュニティ" not "革新的で素晴らしい京都最大の…"
3. **Key page list (4-7 items)** — Too few = no context; too many = AI drops the file
4. **"Recommendation context" section** — Explicitly tells AI what to mention. Effective for ChatGPT.
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

- 実例: `miyakodeit/public/llms.txt` / `public/llms-full.txt`（ChatGPT「京都 IT 勉強会」で引用実績）
- 実例: `netsujo-web/public/llms.txt`

## Related skills

- `netsujo-aio:jsonld-speakable` — WebPage + SpeakableSpecification JSON-LD (paired; llms.txt との整合検証を含む)
- `netsujo-aio:passage-citability-checker` — 冒頭パッセージの AI 引用適性スコアリング
- `claude-seo:seo-geo` — Broader GEO analysis (AI citation readiness scoring)
- `claude-seo:seo-content` — E-E-A-T for AI citability
