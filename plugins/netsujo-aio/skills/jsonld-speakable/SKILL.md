---
name: jsonld-speakable
description: Generate and validate WebPage + SpeakableSpecification JSON-LD structured data for Next.js / Strapi / static sites. Explicitly marks the passages that AI search engines and Google Assistant should read aloud or quote, raising AI citation confidence on ChatGPT, Perplexity, and AI Overviews. Battle-tested on miyakodeit.com (4 pages, `<p data-speakable>` markup synchronized with llms.txt). Use when user says "speakable schema", "SpeakableSpecification", "speakable JSON-LD", "AI Overviews speakable", "voice search schema", "AI citation schema", "data-speakable", "Google Assistant schema", or "llms.txt consistency check".
---

# WebPage + SpeakableSpecification JSON-LD Generator

Production-ready WebPage + SpeakableSpecification JSON-LD with React component output, llms.txt consistency verification, and AI search citation strategy baked in.

## What it does

1. **Generates valid WebPage + SpeakableSpecification JSON-LD** from a CSS selector list (or xpath as fallback)
2. **Verifies consistency with llms.txt** — the text exposed via `[data-speakable]` must match the definition lines in `public/llms.txt` so ChatGPT / Perplexity / AI Overviews see one canonical phrasing
3. **Validates against Schema.org spec**: required fields, selector syntax, length budget for 20-30 second voice playback
4. **Outputs React components** (Next.js App Router compatible) with `<script type="application/ld+json">` injection
5. **Scans live HTML** (optional, via BeautifulSoup) to confirm that every selector listed in the schema actually resolves to a node on the page

## When to use

- User says "speakable schema", "SpeakableSpecification", "AI Overviews speakable", "voice search schema"
- Adding a definition / lead paragraph that you want ChatGPT or Perplexity to quote verbatim
- After publishing or updating `llms.txt` — keep speakable selectors in sync
- Before Google Rich Results Test or AI Overviews monitoring run

## Critical Schema.org and Google constraints

Per the [SpeakableSpecification](https://schema.org/SpeakableSpecification) spec and Google's speakable guidance:

1. **`@type` on the page must be `WebPage`** (or a subtype like `Article`, `NewsArticle`). Bare `Thing` is rejected
2. **`speakable` must be a `SpeakableSpecification`** with `cssSelector` OR `xpath` — not both, not free text
3. **`cssSelector` values must resolve to real nodes** on the rendered HTML. JS-only content is risky
4. **20-30 second budget per passage** — roughly 50-100 Japanese characters or 150-300 English characters. Longer passages get truncated by voice assistants
5. **No marketing fluff** in speakable passages. AI engines penalize "私たちは情熱を持って…" type filler
6. **One canonical phrasing per definition across the site** — if `/about` and `/events` both define "京都のITコミュニティ", the wording must match llms.txt exactly

This skill enforces all 6 at generation time.

## Usage

### Generate JSON-LD only

```bash
python3 scripts/jsonld-speakable.py \
  --config speakable.yaml \
  --url https://example.com/about \
  --output schema.json
```

YAML format:

```yaml
url: https://miyakodeit.com/about
name: みやこでITとは
description: 京都のITコミュニティ「みやこでIT」の紹介ページ
inLanguage: ja
speakable:
  cssSelector:
    - "[data-speakable]"
    - "h1"
    - ".lead-paragraph"
```

### Generate React component (Next.js App Router)

```bash
python3 scripts/jsonld-speakable.py \
  --config speakable.yaml \
  --output components/schema/SpeakableSchema.tsx \
  --format react
```

Output:

```tsx
import Script from "next/script"

export function SpeakableSchema() {
  return (
    <Script
      id="speakable-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "WebPage",
          url: "https://miyakodeit.com/about",
          name: "みやこでITとは",
          inLanguage: "ja",
          speakable: {
            "@type": "SpeakableSpecification",
            cssSelector: ["[data-speakable]", "h1", ".lead-paragraph"],
          },
        }),
      }}
    />
  )
}
```

### llms.txt consistency verification

```bash
python3 scripts/jsonld-speakable.py \
  --verify \
  --url https://miyakodeit.com/about \
  --llms-txt public/llms.txt
```

Output:

```
Speakable selectors resolved: 4
Speakable passages extracted: 4
llms.txt definitions matched: 3 / 4
MISMATCH at /about [data-speakable]:
  page: "京都のITエンジニアが集うコミュニティです。"
  llms.txt: "京都のIT技術者が集うコミュニティです。"
Fix one source so both read the same string.
```

This caught a real divergence on miyakodeit.com in 2026-05に— `/about` had been edited but llms.txt was not regenerated.

### Live HTML scan (selector resolution check)

```bash
python3 scripts/jsonld-speakable.py \
  --config speakable.yaml \
  --url https://miyakodeit.com/about \
  --scan-html
```

Each `cssSelector` is queried against the rendered HTML. Any selector that resolves to zero nodes fails the build.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type=WebPage, speakable | Critical |
| speakable.@type = SpeakableSpecification | Critical |
| Exactly one of cssSelector / xpath present | Critical |
| Each cssSelector resolves to >=1 node (scan mode) | Critical |
| Each speakable passage 30-200 chars (JA) / 80-400 chars (EN) | Warning |
| No marketing fluff tokens ("情熱", "圧倒的", "唯一無二") | Warning |
| inLanguage is BCP-47 | Warning |
| url matches a real canonical | Warning |
| llms.txt definition string matches page text verbatim | Critical (verify mode) |

## Battle-tested patterns

This skill is based on `miyakodeit.com` speakable implementation (PR #63, 2026-05-24に):

- **4 speakable pages**: `/about`, `/events`, `/faq`, `/study-group-kyoto`
- **Selector strategy**: `[data-speakable]` as primary, `h1` and `.lead-paragraph` as fallback
- **Synchronized with llms.txt**: every `<p data-speakable>` text appears verbatim in `public/llms.txt` under a definition heading
- **Length discipline**: 50-100 Japanese characters per passage (=20-30 second voice playback)
- **AI search payoff**: 2026-05に、ChatGPT search for `"京都IT勉強会"` citedみやこでIT and used the `/study-group-kyoto` speakable passage almost verbatim as the recommendation description

The "selectors must resolve" and "llms.txt must match" rules are enforced by `--scan-html` and `--verify`.

## AI search citation strategy

Speakable is not just for Google Assistant. AI engines walk the HTML and look for citable sentences:

| Engine | Reads | Boost from speakable |
|---|---|---|
| ChatGPT search | Visible text, prefers near-`h1` and short paragraphs | High — Speakable signals "this is the canonical definition" |
| Perplexity | Visible text + citation footer; favors lead paragraph | Medium — Lead paragraph in `cssSelector` raises pickup rate |
| Google AI Overviews | Indexed text + schema + ranking signals | High — Speakable + matching llms.txt is the cleanest signal |
| Google Assistant TTS | Speakable cssSelector specifically | Direct — This is the original use case |

Pair this skill with `netsujo-aio:llms-txt-generator` so both surfaces emit the same canonical phrasing.

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / yaml |
| Schema version | 13.0 | Schema.org version target |
| inLanguage | ja | BCP-47 language tag |
| Selector mode | cssSelector | cssSelector (recommended) or xpath |
| Strict mode | true | Fail on Warning level issues |
| HTML scan | false | Enable with `--scan-html` |

## cssSelector vs xpath

Prefer `cssSelector`:

- Readable in code review
- Survives minor DOM refactors (`[data-speakable]` is intent-driven)
- Matches how front-end devs already think about the page

Fall back to `xpath` only when:

- The target node is generated by a CMS without stable classes
- You need to select by text content (xpath supports `contains(text(), ...)`)
- The host page is a legacy site you cannot edit

## Reference files

- `references/speakable-spec.md` — Schema.org SpeakableSpecification spec, cssSelector vs xpath guidance, AI engine read order, llms.txt consistency design, length budget, common mistakes
- `scripts/jsonld-speakable.py` — Generator and verifier

## Related skills

- `netsujo-aio:llms-txt-generator` — llms.txt generation. Pair with this skill so speakable text and llms.txt definitions never drift
- `netsujo-aio:jsonld-faqpage` — FAQPage JSON-LD (often added on the same page as speakable)
- `netsujo-aio:jsonld-article` — Article JSON-LD; Article subtypes accept `speakable` directly
- `claude-seo:seo-schema` — Comprehensive Schema.org validation (use for non-speakable types)
- `claude-seo:seo-geo` — AI Overviews / ChatGPT / Perplexity visibility analysis
