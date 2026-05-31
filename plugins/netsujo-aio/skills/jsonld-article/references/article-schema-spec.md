# Article / BlogPosting / NewsArticle — Schema.org & Google Rich Results Spec

Reference excerpts and cheat-sheet for the `jsonld-article` skill. Source of truth: [Schema.org Article](https://schema.org/Article) and [Google Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article).

## Subtype hierarchy

```
CreativeWork
└── Article
    ├── BlogPosting          → editorial blog entries
    │   └── LiveBlogPost
    ├── NewsArticle          → time-sensitive journalism / press releases
    │   ├── ReportageNewsArticle
    │   ├── AnalysisNewsArticle
    │   ├── BackgroundNewsArticle
    │   └── OpinionNewsArticle
    ├── ScholarlyArticle     → academic / peer-reviewed
    ├── TechArticle
    ├── Report
    └── SatiricalArticle
```

## Subtype differences

| Field | Article | BlogPosting | NewsArticle |
|---|---|---|---|
| Primary use | Generic editorial | Personal/company blog | News, press release |
| `datePublished` weight | Normal | Normal | High (freshness signal) |
| `dateline` field | — | — | Recommended (location of reporting) |
| `printSection` / `printEdition` | — | — | Optional (print provenance) |
| Google rich result eligibility | Yes | Yes | Yes |
| Top Stories carousel eligibility | No | No | Yes (AMP no longer required as of 2026) |

Selection rule: if unsure, use `Article`. Google treats it as a superset and the visual rich result is identical for `Article` vs `BlogPosting`.

## Required fields (Google)

| Field | Type | Notes |
|---|---|---|
| `@context` | URL | Always `https://schema.org` |
| `@type` | Text | One of Article / BlogPosting / NewsArticle |
| `headline` | Text | ≤ 110 characters |
| `datePublished` | DateTime | ISO 8601 **with timezone offset** |
| `author` | Person or Organization | Must have `@type` set |

## Recommended fields (Google)

| Field | Type | Notes |
|---|---|---|
| `dateModified` | DateTime | ISO 8601 with timezone; ≥ datePublished |
| `image` | ImageObject or URL | width ≥ 696px, aspect ratio 16:9 / 4:3 / 1:1 |
| `publisher` | Organization | Must include `logo` as ImageObject |
| `publisher.logo` | ImageObject | Bounded by 600x60px |
| `description` | Text | 50–160 chars recommended for SERP usage |
| `mainEntityOfPage` | URL or WebPage | Canonical URL of the article |
| `articleBody` | Text | Full body text (powers passage citation in LLMs) |
| `wordCount` | Integer | Auto-compute from articleBody |
| `inLanguage` | Text | BCP-47 (`ja`, `en-US`, `ja-JP`) |
| `keywords` | Text | Comma-separated topic keywords |

## Image aspect ratio reference

Google accepts these three ratios. Width must be ≥ 696px for any of them.

| Ratio | Common sizes (width × height) |
|---|---|
| 16:9 | 1280×720, 1600×900, 1920×1080 |
| 4:3 | 800×600, 1024×768, 1280×960 |
| 1:1 | 800×800, 1080×1080, 1200×1200 |

Provide all three when possible by emitting `image` as an array of ImageObjects — Google will pick the ratio best fit for the result surface.

## ISO 8601 timezone examples

| Form | Valid? | Notes |
|---|---|---|
| `2026-05-31` | No | Date only, no time, no timezone |
| `2026-05-31T09:00:00` | No | Missing timezone |
| `2026-05-31T09:00:00Z` | Yes | UTC |
| `2026-05-31T09:00:00+09:00` | Yes | JST (preferred for ja content) |
| `2026-05-31T09:00:00.123+09:00` | Yes | Fractional seconds OK |

Skill default timezone: `+09:00` (JST). Override via `--timezone` in future versions.

## Common mistakes (caught by validator)

### 1. Missing timezone on datePublished

```json
{ "datePublished": "2026-05-31" }
```

Google emits "Invalid date" in Rich Results Test. Fix:

```json
{ "datePublished": "2026-05-31T09:00:00+09:00" }
```

### 2. Publisher logo exceeds 600x60px

```json
{ "publisher": { "logo": { "url": "...", "width": 1200, "height": 300 } } }
```

The whole `Article` rich result becomes ineligible. Fix: serve a separate logo asset constrained to 600x60.

### 3. Headline over 110 characters

```json
{ "headline": "AI×ブロックチェーンが企業にもたらす5つの変革と導入時に気をつけたい落とし穴のすべて2026年版" }
```

Google truncates display and may suppress the rich result. Fix: shorten or split into `headline` (≤110) + `alternativeHeadline`.

### 4. String-only author

```json
{ "author": "飯田友広" }
```

Ignored by Google. Fix:

```json
{ "author": { "@type": "Person", "name": "飯田友広", "url": "https://miyakodeit.com/about" } }
```

### 5. Image too narrow

```json
{ "image": "https://example.com/thumb-400.jpg" }
```

400px width fails the 696px minimum. Fix: provide a hero image ≥ 696px wide, or emit an ImageObject array with the largest variant first.

### 6. mainEntityOfPage mismatched with canonical

```json
{ "mainEntityOfPage": "https://example.com/blog/post" }
```

…while the page's `<link rel="canonical">` is `https://example.com/blog/post/`. Trailing-slash mismatches cause Google to drop the schema. Fix: match canonical exactly, including protocol, host, and trailing slash.

### 7. dateModified before datePublished

A modification timestamp earlier than publication is invalid and signals a bug in the publishing pipeline. Validator emits a Warning.

## Strapi v5 mapping notes

When `--format strapi`, the generator emits a component at `seo.article-schema` with attributes:

| JSON-LD field | Strapi type |
|---|---|
| headline | string (required, max 110) |
| datePublished | datetime (required) |
| dateModified | datetime |
| description | text |
| image | media (single, images) |
| author | relation to `api::author.author` |
| publisher | relation to `api::organization.organization` |
| inLanguage | enumeration (`ja`, `en`, ...) |
| articleBody | richtext |

Strapi's `datetime` type stores ISO 8601 with UTC; the renderer must add the publication timezone on the front-end.
