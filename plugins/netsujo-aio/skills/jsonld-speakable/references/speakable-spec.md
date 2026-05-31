# SpeakableSpecification — Spec, Strategy, and Pitfalls

Reference notes for the `jsonld-speakable` skill. Source of truth for what to put inside `speakable` and why.

## 1. Schema.org definition

`SpeakableSpecification` indicates sections of a `WebPage` (or its subtypes such as `Article`, `NewsArticle`) that are suitable for text-to-speech playback. It originated for Google Assistant audio answers but is now also read by AI search crawlers as a "canonical citation hint".

Minimum required shape:

```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://example.com/about",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": ["[data-speakable]", "h1"]
  }
}
```

- `@type` of the parent **must** be `WebPage` or a subtype. `Thing` and bare `CreativeWork` are not accepted by Google Rich Results.
- `speakable` accepts `cssSelector` OR `xpath`. Pick one. Mixing both is undefined behavior.
- `inLanguage` is recommended (`ja`, `en-US`, etc.) — the AI engines route to language-specific renderers.

## 2. cssSelector vs xpath — how to choose

Prefer `cssSelector`. It is readable in code review, survives minor DOM refactors, and matches how front-end devs think about the page.

| Criterion | cssSelector | xpath |
|---|---|---|
| Readability | High | Low |
| Intent-driven attributes (`[data-speakable]`) | Native | Awkward |
| Text-content matching | Not supported | Supported via `contains(text(), ...)` |
| CMS-generated unstable classes | Need stable hook | Can target by structure |
| Tooling support | Universal | Universal but verbose |

Fall back to `xpath` only when (a) the host page is a legacy CMS without stable hooks, or (b) you must select by text content. For greenfield Next.js / Strapi sites, always add a `data-speakable` attribute and use cssSelector.

## 3. AI engine read order

Modern AI search engines do not all read schema the same way. The practical priority order observed in 2026:

1. **Google AI Overviews** — Uses the indexed page text, ranking signals, and schema. Speakable + matching llms.txt is the cleanest "this is the definition" signal.
2. **ChatGPT search** — Walks visible text, prefers short paragraphs near `h1` and elements with semantic hooks. Speakable raises confidence that the passage is canonical.
3. **Perplexity** — Walks visible text, includes citation footer. Lead paragraphs in `cssSelector` get higher pickup rates.
4. **Google Assistant TTS** — Speakable cssSelector is the original use case. Voice output reads selectors in document order.

In all four cases, the win comes from giving the engine a short, citable, marketing-free sentence. Speakable schema is the label; the page text is the content. Both must be present.

## 4. llms.txt consistency — the design rule

The cardinal rule: **the text behind every speakable selector must appear verbatim in `public/llms.txt`**.

Why:

- AI engines that fetch `/llms.txt` (Perplexity, several emerging crawlers) compare what they read there to what they see on the page. Mismatch costs trust.
- Internally, drift between marketing copy on the page and llms.txt is the #1 source of "AI is quoting an outdated description" complaints.
- The skill's `--verify` mode treats any mismatch as Critical.

Design pattern:

1. Author the canonical definition once in a YAML data file (`data/definitions.yaml`)
2. Generator A renders `<p data-speakable>{{definition}}</p>` into the page component
3. Generator B renders the same string into `public/llms.txt` under a definition heading
4. CI runs `python3 jsonld-speakable.py --verify ...` on every PR

This is exactly the pattern shipped on miyakodeit.com in PR #63 on 2026-05-24に.

## 5. Length budget — 20 to 30 seconds of voice

Google Assistant truncates speakable passages that exceed roughly 30 seconds of TTS. The character budget:

| Language | 20s floor | 30s ceiling | Sweet spot |
|---|---|---|---|
| Japanese (JA) | ~30 chars | ~100 chars | 50-80 chars |
| English (EN) | ~80 chars | ~300 chars | 150-220 chars |

Below the floor: AI engines see the passage as a fragment and rarely cite it. Above the ceiling: voice playback truncates mid-sentence and AI engines truncate at the first period. Aim for one complete sentence in the sweet spot.

## 6. Common mistakes (caught in real audits)

1. **Different text on different pages**. `/about` reads "京都のITコミュニティ" while `/events` reads "京都のIT技術者コミュニティ". AI engines cite whichever they crawled most recently — the user experience looks inconsistent.
2. **Marketing fluff inside speakable**. "情熱を持って京都のIT業界を盛り上げます" gets penalized. Speakable should be a definition, not a slogan.
3. **Selectors that resolve to zero nodes**. The schema lists `.lead-paragraph` but the component never renders that class. Validators do not catch this; only `--scan-html` does.
4. **Mixing cssSelector and xpath in one SpeakableSpecification**. Behavior is undefined. Pick one.
5. **JS-only content**. The `[data-speakable]` element is mounted by `useEffect`. Server-rendered crawlers miss it. Always render the speakable text on the server.
6. **Forgetting to update llms.txt** after a page copy change. Run `--verify` in CI to block the merge.
7. **Multiple `data-speakable` elements with conflicting definitions on the same page**. Pick one canonical sentence per page.
8. **Using `@type: Thing` or `@type: CreativeWork`**. Speakable only validates on `WebPage` and its subtypes (`Article`, `NewsArticle`, `BlogPosting`, etc.).

## 7. Related signals to ship alongside

- `Article.speakable` for blog posts — same shape, parent is `Article` instead of `WebPage`
- `BreadcrumbList` — helps AI engines understand the page hierarchy
- `FAQPage` — pair with speakable so the question/answer pair is both quotable and citable
- `llms.txt` — the matching plaintext surface
- `Organization` JSON-LD — gives the AI engine the "who" behind the citation
