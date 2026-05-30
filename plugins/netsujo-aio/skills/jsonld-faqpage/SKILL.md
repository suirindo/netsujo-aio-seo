---
name: jsonld-faqpage
description: Generate and validate FAQPage JSON-LD structured data for Next.js / Strapi / static sites. Detects Q&A duplication across pages, validates against Schema.org spec, and produces drop-in React components. Battle-tested on miyakodeit.com (6 categories, 31 questions). Use when user says "FAQ schema", "FAQPage JSON-LD", "FAQ structured data", "rich results FAQ", or has multiple FAQ pages with overlap risk.
---

# FAQPage JSON-LD Generator

Production-ready FAQPage JSON-LD with React component output, duplicate-question detection across pages, and Google Rich Results compatibility checks.

## What it does

1. **Generates valid FAQPage JSON-LD** from a list of Q&A pairs
2. **Detects duplicate questions** across multiple FAQ pages (Google ignores duplicates and may penalize)
3. **Validates against Schema.org spec**: required fields, character limits, prohibited markup
4. **Outputs React components** (Next.js App Router compatible) with `<script type="application/ld+json">` injection
5. **Cross-references existing FAQs** to suggest unique question rewrites for sub-pages

## When to use

- User says "FAQ schema", "FAQPage JSON-LD", "rich results FAQ"
- Adding FAQ section to a new page when site already has `/faq`
- After moving FAQ content between pages (canonical migration)
- Before Google Rich Results Test submission

## Critical Google constraints

Per [Google FAQPage guidelines](https://developers.google.com/search/docs/appearance/structured-data/faqpage):

1. **No duplicate questions across pages on the same site** — Google picks one or drops both
2. **No marketing content in answers** — answer must be the actual answer text
3. **Must be visible on the page** — JSON-LD only, no hidden FAQ
4. **No nested questions** — flat Q&A only
5. **HTML in answers**: only `<p>`, `<a>`, `<br>`, `<ol>`, `<ul>`, `<li>`, `<strong>`, `<em>` allowed

This skill enforces all 5 at generation time.

## Usage

### Generate JSON-LD only

```bash
python3 scripts/jsonld-faqpage.py \
  --input faq-data.yaml \
  --output schema.json
```

YAML format:

```yaml
- question: 京都でIT勉強会に参加するにはどうすればいいですか？
  answer: みやこでITのconnpassページから募集中のイベントを選び、参加申込をしてください。
- question: 一人で参加しても大丈夫ですか？
  answer: 大丈夫です。初参加の方も多く、開始時に簡単な自己紹介を行います。
```

### Generate React component (Next.js App Router)

```bash
python3 scripts/jsonld-faqpage.py \
  --input faq-data.yaml \
  --output components/faq/FAQPageSchema.tsx \
  --format react
```

Output:

```tsx
import Script from "next/script"

export function FAQPageSchema() {
  return (
    <Script
      id="faqpage-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "FAQPage",
          mainEntity: [...]
        }),
      }}
    />
  )
}
```

### Cross-page duplicate detection

```bash
python3 scripts/jsonld-faqpage.py \
  --scan-existing https://example.com/faq \
  --input new-faq.yaml \
  --check-duplicates
```

Output:

```
Found 3 duplicate questions:
- "What is FAQ?" already exists in /faq line 12
- "How to contact?" already exists in /support line 5
```

This caught a real issue on miyakodeit.com where `/guides/kyoto-mokumoku` initially had the same 5 questions as `/faq`. Now the guide has 5 unique SEO-targeted questions.

### Multi-language (i18n) support

```bash
python3 scripts/jsonld-faqpage.py \
  --input faq-ja.yaml \
  --input-en faq-en.yaml \
  --inLanguage ja
```

Produces `inLanguage: "ja"` per Schema.org spec.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type, mainEntity | Critical |
| mainEntity not empty | Critical |
| Each item: @type=Question, name, acceptedAnswer.text | Critical |
| Question name length 10-300 chars | Warning |
| Answer text length 10-2000 chars | Warning |
| Prohibited HTML tags in answer | Critical |
| No duplicate questions within page | Critical |
| Inline links use https | Warning |

## Battle-tested patterns

This skill is based on `miyakodeit.com` FAQ implementation:
- 6 categories: 初参加 / イベント参加 / 会場 / 技術レベル / Discord / 連携
- 31 questions total (4-13 per category)
- All questions cross-checked across `/faq`, `/first-time`, `/study-group-kyoto`, `/guides/kyoto-mokumoku`
- No duplicates between pages (each page has unique angle)
- Anchor links from sub-pages back to `/faq#category` via fragment IDs

The "no duplicates between pages" rule is enforced by `--check-duplicates`.

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / yaml |
| Schema version | 13.0 | Schema.org version target |
| inLanguage | ja | BCP-47 language tag |
| Strict mode | true | Fail on Warning level issues |

## Reference files

- `references/faqpage-schema-spec.md` — Full Schema.org spec excerpts with examples
- `references/rich-results-test.md` — How to test in Google Rich Results Test
- `references/cross-page-strategy.md` — How to avoid duplicates while ranking multiple FAQ pages
- `scripts/jsonld-faqpage.py` — Generator

## Related skills

- `netsujo-aio:jsonld-organization` — Organization JSON-LD (often paired with FAQPage)
- `netsujo-aio:jsonld-article` — Article JSON-LD for blog/news
- `netsujo-aio:jsonld-breadcrumb` — BreadcrumbList JSON-LD
- `claude-seo:seo-schema` — Comprehensive Schema.org validation (use for non-FAQ types)
