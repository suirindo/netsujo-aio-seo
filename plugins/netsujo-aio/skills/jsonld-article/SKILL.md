---
name: jsonld-article
description: Generate and validate Article / BlogPosting / NewsArticle JSON-LD structured data for Next.js / Strapi / static sites. Auto-detects subtype, enforces Google rich results requirements (headline length, image aspect ratio, publisher logo size, ISO 8601 timezone), and produces drop-in React components. Battle-tested on miyakodeit.com blog (Article schema across all /blog/* posts, with ChatGPT and Perplexity citation hits). Use when user says "Article schema", "BlogPosting JSON-LD", "NewsArticle structured data", "article rich results", "blog post schema", "author markup", "publisher markup", or is adding JSON-LD to a blog/news/article page.
---

# Article / BlogPosting / NewsArticle JSON-LD Generator

Production-ready Article-family JSON-LD with React component output, Google Rich Results validation, and batch generation for content directories.

## What it does

1. **Generates valid Article JSON-LD** in three subtypes — `Article` (default), `BlogPosting`, `NewsArticle`
2. **Enforces Google Rich Results requirements**: headline length, image aspect ratios, publisher logo dimensions, ISO 8601 datestamps with timezone
3. **Auto-computes `wordCount`** from `articleBody` when not supplied
4. **Outputs three formats**: raw JSON, Next.js React component, Strapi v5 component definition
5. **Batch mode**: walk a content directory (`./content/blog/`) and emit one JSON-LD per markdown file

## When to use

- User says "Article schema", "BlogPosting JSON-LD", "NewsArticle structured data", "blog post schema"
- Adding JSON-LD to a Next.js blog post template
- Migrating Strapi v5 blog content and need matching schema component
- Before submitting an article URL to Google Rich Results Test
- Optimizing for ChatGPT / Perplexity citation eligibility (Article schema improves passage attribution)

## Subtype selection

Per [Schema.org Article hierarchy](https://schema.org/Article):

```
Article
├── BlogPosting   → personal / editorial blog entries
│   └── LiveBlogPost
├── NewsArticle   → time-sensitive news (date matters more)
│   ├── ReportageNewsArticle
│   └── AnalysisNewsArticle
└── ScholarlyArticle → academic / peer-reviewed
```

Selection guide (used by `--type auto`):

| Content type | Subtype |
|---|---|
| Personal blog, company blog, editorial | `BlogPosting` |
| Press release, breaking news, dated reportage | `NewsArticle` |
| Generic editorial content, evergreen guides | `Article` |

If unsure, `Article` is the safe default — Google treats it as a superset.

## Critical Google constraints

Per [Google Article rich results guidelines](https://developers.google.com/search/docs/appearance/structured-data/article):

1. **`headline` must be 110 characters or fewer** — Google truncates beyond this
2. **`image` minimum width 696px** AND aspect ratio one of `16:9`, `4:3`, `1:1`
3. **`publisher.logo` must fit within 600x60px** — width AND height bounded
4. **`datePublished` and `dateModified` must be ISO 8601 with timezone offset** — `2026-05-31T09:00:00+09:00`, not `2026-05-31`
5. **`author` must be `Person` or `Organization`** with `@type` set — string-only authors are ignored
6. **`mainEntityOfPage`** should be the canonical article URL

This skill enforces all 6 at generation time. Strict mode fails the build; non-strict mode emits warnings.

## Usage

### Generate JSON-LD only

```bash
python3 scripts/jsonld-article.py \
  --input article.md \
  --output schema.json
```

Markdown frontmatter format:

```yaml
---
title: AI×ブロックチェーンが企業にもたらす5つの変革
description: 企業がAIとブロックチェーンを組み合わせる実例と導入手順
datePublished: 2026-05-31T09:00:00+09:00
dateModified: 2026-05-31T18:30:00+09:00
author:
  type: Person
  name: 飯田友広
  url: https://miyakodeit.com/about
publisher:
  type: Organization
  name: みやこでIT
  logo: https://miyakodeit.com/logo.png
image: https://miyakodeit.com/blog/ai-blockchain/hero.jpg
url: https://miyakodeit.com/blog/ai-blockchain
type: BlogPosting
inLanguage: ja
---

本文がここに続く ...
```

### Generate React component (Next.js App Router)

```bash
python3 scripts/jsonld-article.py \
  --input article.md \
  --output components/blog/ArticleSchema.tsx \
  --format react
```

Output:

```tsx
import Script from "next/script"

export function ArticleSchema() {
  return (
    <Script
      id="article-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "BlogPosting",
          headline: "...",
          datePublished: "...",
          author: { "@type": "Person", name: "..." },
          publisher: { "@type": "Organization", name: "...", logo: { "@type": "ImageObject", url: "..." } },
          image: "...",
          mainEntityOfPage: "...",
          inLanguage: "ja",
        }),
      }}
    />
  )
}
```

### Generate Strapi v5 component

```bash
python3 scripts/jsonld-article.py \
  --input article.md \
  --output strapi/components/seo/article-schema.json \
  --format strapi
```

Produces a Strapi v5 component schema (`uid: seo.article-schema`) with fields mapped to Strapi types — useful when articles live in Strapi and the schema is rendered server-side at request time.

### Subtype override

```bash
python3 scripts/jsonld-article.py \
  --input press-release.md \
  --type NewsArticle \
  --inLanguage ja \
  --output schema.json
```

### Batch generation

```bash
python3 scripts/jsonld-article.py \
  --batch ./content/blog/ \
  --output ./public/jsonld/ \
  --format json
```

Walks `./content/blog/**/*.md`, emits one `.json` per source file mirroring the directory structure. Useful for static-site builds that pre-render JSON-LD as separate files.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type, headline, datePublished, author | Critical |
| @type ∈ {Article, BlogPosting, NewsArticle} | Critical |
| headline ≤ 110 characters | Warning |
| datePublished is ISO 8601 with timezone | Critical |
| dateModified ≥ datePublished | Warning |
| image width ≥ 696px (if dimensions known) | Warning |
| image aspect ratio ∈ {16:9, 4:3, 1:1} | Warning |
| publisher.logo within 600x60px | Warning |
| author has @type (Person or Organization) | Critical |
| mainEntityOfPage present and is canonical URL | Warning |
| inLanguage is valid BCP-47 tag | Warning |
| articleBody non-empty if supplied | Warning |

Strict mode (`--strict`) treats all Warnings as Critical.

## Battle-tested patterns

This skill is derived from `miyakodeit.com` blog Article JSON-LD:
- All `/blog/*` posts emit `BlogPosting` schema
- `author` is `Person` with `url` pointing to `/about`
- `publisher` is the `Organization` with logo at exactly 600x60px (logo-jsonld.png)
- `datePublished` always carries `+09:00` timezone
- `mainEntityOfPage` matches the canonical URL exactly (no trailing slash mismatch)
- Article schema validated weekly by `gsc-weekly-audit.py`

ChatGPT and Perplexity citation hits increased measurably after enforcing `author.url` and `publisher.logo` — both AI engines use author/publisher attribution when surfacing passages.

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / strapi |
| Subtype | Article | Article / BlogPosting / NewsArticle / auto |
| inLanguage | ja | BCP-47 language tag |
| Strict mode | false | Fail on Warning level issues |
| Word count | auto | Compute from articleBody if present |
| Timezone | +09:00 | Default timezone when frontmatter omits it (fails in strict) |

## Reference files

- `references/article-schema-spec.md` — Article / BlogPosting / NewsArticle differences, image aspect ratio reference, common mistakes
- `scripts/jsonld-article.py` — Generator

## Related skills

- `netsujo-aio:jsonld-faqpage` — FAQPage JSON-LD (often paired on blog posts with FAQ sections)
- `netsujo-aio:jsonld-organization` — Organization JSON-LD (referenced by Article.publisher)
- `netsujo-aio:jsonld-breadcrumb` — BreadcrumbList JSON-LD for article navigation
- `claude-seo:seo-schema` — Comprehensive Schema.org validation across all types
