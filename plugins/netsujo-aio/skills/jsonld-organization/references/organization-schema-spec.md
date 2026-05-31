# Schema.org Organization — Spec Excerpts

Reference extract for the `jsonld-organization` skill. Sources: [schema.org/Organization](https://schema.org/Organization), [Google Organization structured data](https://developers.google.com/search/docs/appearance/structured-data/organization), [Google logo guidelines](https://developers.google.com/search/docs/appearance/structured-data/logo).

## Required fields (Schema.org + Google)

| Field | Type | Notes |
|---|---|---|
| `@context` | URL | Must be `https://schema.org` |
| `@type` | Text | `Organization` (or a subtype: `Corporation`, `NGO`, `LocalBusiness`, ...) |
| `name` | Text | Legal or commonly-known name. 1-150 chars recommended |
| `url` | URL | Canonical homepage. Must be absolute https |

## Strongly recommended (for Google rich results + AI citation)

| Field | Type | Notes |
|---|---|---|
| `logo` | URL or ImageObject | Min 112x112px. Absolute URL. PNG/JPG/WebP. Square preferred |
| `image` | URL | Should match `logo` or be a superset |
| `description` | Text | 50-300 chars. Used by ChatGPT / Perplexity citations |
| `sameAs` | URL[] | Canonical SNS / Wikipedia / Wikidata profile URLs |
| `foundingDate` | Date | ISO 8601 (`YYYY-MM-DD`) |
| `founder` | Person[] | Each with `name` and `url` |
| `address` | PostalAddress | See PostalAddress below |
| `contactPoint` | ContactPoint[] | See ContactPoint below |
| `legalName` | Text | Full legal entity name when `name` is the brand |
| `taxID` / `vatID` | Text | For B2B / e-commerce |
| `numberOfEmployees` | QuantitativeValue | Optional |
| `slogan` | Text | Optional brand tagline |

## PostalAddress fields

| Field | Required by Google | Notes |
|---|---|---|
| `streetAddress` | Recommended | "中京区..." or "1-2-3 Karasuma" |
| `addressLocality` | Recommended | City |
| `addressRegion` | Recommended | Prefecture / state |
| `postalCode` | Recommended | "604-XXXX" |
| `addressCountry` | **Required** | ISO 3166-1 alpha-2 (`JP`, `US`, ...) |

## ContactPoint fields

| Field | Required | Notes |
|---|---|---|
| `@type` | Required | `ContactPoint` |
| `contactType` | **Required** | `customer support`, `sales`, `technical support`, `billing support`, `bookings`, `reservations`, `credit card support`, `emergency`, `baggage tracking`, `roadside assistance`, `package tracking` |
| `telephone` | One of | E.164 format (`+81-75-XXX-XXXX`) |
| `email` | One of | At least one of telephone / email required |
| `areaServed` | Recommended | ISO 3166 country code or region |
| `availableLanguage` | Recommended | BCP-47 (`ja`, `en`) |

## Google Rich Results — critical constraints

1. **`logo` min dimensions: 112x112px.** Smaller logos are silently dropped from the knowledge panel.
2. **All URLs must be absolute.** Relative paths (`/logo.png`) fail validation.
3. **`logo` and `image` should match** for entity confidence.
4. **`sameAs` must be canonical profile URLs** — no `bit.ly`, no redirects, no login-walled pages, no `linktr.ee`.
5. **Single Organization per origin.** Emit once in root layout, not per-page. Duplicate nodes confuse entity resolution.
6. **`@id` recommended** — use the canonical URL with `#organization` fragment (e.g. `https://example.com/#organization`) to enable cross-document references from `Article.publisher`.

## sameAs — recommended platforms

Ordered by AI citation weight (ChatGPT / Perplexity / Google AI Overviews observation, 2026):

1. **Wikipedia** — highest citation weight, hardest to earn
2. **Wikidata** — `https://www.wikidata.org/wiki/Q...`
3. **LinkedIn company page** — `https://www.linkedin.com/company/<slug>`
4. **GitHub org** — `https://github.com/<org>` (for tech companies)
5. **X (formerly Twitter)** — `https://x.com/<handle>`
6. **Crunchbase** — for funded startups
7. **YouTube channel** — `https://www.youtube.com/@<channel>`
8. **Facebook page** — `https://www.facebook.com/<page>`
9. **Instagram** — `https://www.instagram.com/<handle>/`
10. **Industry-specific**: connpass (JP tech), note (JP publishing), Behance (design), Dribbble (design), Stack Overflow Teams (tech)

## Minimal valid example

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Netsujo Inc.",
  "url": "https://netsujo.jp/"
}
```

## Production example (netsujo.jp pattern)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://netsujo.jp/#organization",
  "name": "Netsujo Inc.",
  "legalName": "株式会社Netsujo",
  "url": "https://netsujo.jp/",
  "logo": "https://netsujo.jp/logo.png",
  "image": "https://netsujo.jp/logo.png",
  "description": "Netsujoは地域コミュニティとIT人材育成を結ぶ会社です。京都を拠点にIT勉強会・受託開発・SaaS開発を行います。",
  "foundingDate": "2024-08-08",
  "founder": [
    {
      "@type": "Person",
      "name": "飯田友広",
      "url": "https://netsujo.jp/about#founder"
    }
  ],
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "京都市",
    "addressRegion": "京都府",
    "addressCountry": "JP"
  },
  "contactPoint": [
    {
      "@type": "ContactPoint",
      "contactType": "customer support",
      "email": "contact@netsujo.jp",
      "areaServed": "JP",
      "availableLanguage": ["ja", "en"]
    }
  ],
  "sameAs": [
    "https://github.com/netsujo",
    "https://x.com/netsujo_inc",
    "https://www.linkedin.com/company/netsujo",
    "https://miyakodeit.connpass.com/",
    "https://note.com/netsujo"
  ]
}
```

## Subtypes to consider

- `Corporation` — publicly traded / large enterprise
- `LocalBusiness` — has physical storefront (requires `geo`, `openingHoursSpecification`)
- `NGO` — non-profit
- `EducationalOrganization` — school / university
- `GovernmentOrganization` — public sector
- `NewsMediaOrganization` — publishers (used by Google News)
- `OnlineBusiness` — internet-only

When in doubt, use plain `Organization`. Subtypes are additive — `LocalBusiness` is an `Organization`, so it inherits all fields above.

## Validation tools

- [Google Rich Results Test](https://search.google.com/test/rich-results) — runtime validation
- [Schema Markup Validator](https://validator.schema.org/) — spec validation
- `--verify <url>` flag of this skill — automated CI check
