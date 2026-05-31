---
name: jsonld-organization
description: Generate and validate Organization JSON-LD structured data for Next.js / Strapi / static sites. Auto-expands sameAs from GitHub / X / LinkedIn / connpass / note handles, validates logo dimensions for Google rich results, and produces drop-in React components. Battle-tested on netsujo.jp as the citation source for ChatGPT search "Netsujo" queries. Use when user says "Organization schema", "Organization JSON-LD", "company schema", "about page schema", "brand schema", "sameAs", "logo schema", "rich results organization", or is wiring up `/company`, `/about`, or the site root for AI citation.
---

# Organization JSON-LD Generator

Production-ready Organization JSON-LD with React component output, sameAs auto-expansion from social handles, and Google Rich Results logo validation.

## What it does

1. **Generates valid Organization JSON-LD** from a company profile config (YAML or JSON)
2. **Auto-expands sameAs** from short handles (GitHub / X / LinkedIn / connpass / note / Facebook / YouTube / Instagram) into full URLs
3. **Validates against Schema.org spec**: required fields, URL format, recommended fields for AI citation
4. **Outputs React components** (Next.js App Router compatible) with `<script type="application/ld+json">` injection
5. **Verifies logo dimensions** against Google's 112x112px minimum (requires Pillow if local file, HEAD request if URL)
6. **Live-verifies deployed pages** by fetching the URL and parsing existing Organization JSON-LD

## When to use

- User says "Organization schema", "company JSON-LD", "about page schema", "brand schema", "sameAs"
- Wiring up the root layout, `/company`, or `/about` for AI search citation (ChatGPT, Perplexity, Google AI Overviews)
- After a logo / NAP / SNS profile change — schema must be updated together with visible content
- Before Google Rich Results Test submission for sitelinks search box / logo display

## Critical Google constraints

Per [Google Organization structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/organization):

1. **`logo` must be at least 112x112px** — smaller logos are silently dropped from knowledge panel
2. **All URLs must be absolute** — `/logo.png` will fail validation, must be `https://example.com/logo.png`
3. **`logo` and `image` should match** — Google uses both, mismatches reduce confidence
4. **`sameAs` must point to canonical profile URLs** — shortened links, redirects, and login-walled pages are ignored
5. **Single Organization per origin** — duplicate Organization nodes across pages confuse entity resolution; emit once in root layout, not per page

This skill enforces all 5 at generation time.

## Usage

### Generate JSON-LD only

```bash
python3 scripts/jsonld-organization.py \
  --config org.yaml \
  --output schema.json
```

YAML format:

```yaml
name: Netsujo Inc.
legalName: 株式会社Netsujo
url: https://netsujo.jp/
logo: https://netsujo.jp/logo.png
description: Netsujoは地域コミュニティとIT人材育成を結ぶ会社です。
foundingDate: 2024-08-08
founder:
  - name: 飯田友広
    url: https://netsujo.jp/about
address:
  streetAddress: 中京区
  addressLocality: 京都市
  addressRegion: 京都府
  postalCode: 604-XXXX
  addressCountry: JP
contactPoint:
  - contactType: customer support
    email: contact@netsujo.jp
    areaServed: JP
    availableLanguage: [ja, en]
sameAs:
  - github:netsujo
  - x:netsujo_inc
  - linkedin:company/netsujo
  - connpass:miyakodeit
  - note:netsujo
```

### Generate React component (Next.js App Router)

```bash
python3 scripts/jsonld-organization.py \
  --config org.yaml \
  --output components/schema/OrgSchema.tsx \
  --format react
```

Output:

```tsx
import Script from "next/script"

export function OrgSchema() {
  return (
    <Script
      id="organization-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Organization",
          name: "Netsujo Inc.",
          url: "https://netsujo.jp/",
          logo: "https://netsujo.jp/logo.png",
          sameAs: [
            "https://github.com/netsujo",
            "https://x.com/netsujo_inc",
            "https://www.linkedin.com/company/netsujo",
            "https://miyakodeit.connpass.com/",
            "https://note.com/netsujo",
          ],
        }),
      }}
    />
  )
}
```

Drop `<OrgSchema />` into `app/layout.tsx` (root) — not per-page.

### sameAs auto-expansion

Short handle → canonical URL mapping:

| Prefix | Expands to |
|---|---|
| `github:<handle>` | `https://github.com/<handle>` |
| `x:<handle>` | `https://x.com/<handle>` |
| `twitter:<handle>` | `https://x.com/<handle>` (normalized) |
| `linkedin:<path>` | `https://www.linkedin.com/<path>` |
| `connpass:<group>` | `https://<group>.connpass.com/` |
| `note:<handle>` | `https://note.com/<handle>` |
| `facebook:<page>` | `https://www.facebook.com/<page>` |
| `youtube:<channel>` | `https://www.youtube.com/@<channel>` |
| `instagram:<handle>` | `https://www.instagram.com/<handle>/` |

Fully-qualified URLs in `sameAs` pass through unchanged.

### Verify a deployed page

```bash
python3 scripts/jsonld-organization.py \
  --verify https://netsujo.jp/
```

Fetches the URL, extracts all `<script type="application/ld+json">` blocks, finds the Organization node, and reports:

```
Organization found at https://netsujo.jp/
  name: Netsujo Inc.            OK
  url: https://netsujo.jp/      OK
  logo: ...netsujo.jp/logo.png  OK (240x240, >= 112x112)
  sameAs: 5 profiles            OK
  description: present          OK
  contactPoint: 1 entry         OK
```

This caught a real issue on netsujo.jp where the staging build emitted a relative `/logo.png` in `logo` — Google rich results test rejected it silently until verified.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type, name, url | Critical |
| url is absolute https | Critical |
| logo is absolute URL | Critical |
| logo image >= 112x112px (if reachable) | Warning |
| name length 1-150 chars | Warning |
| description length 50-300 chars | Warning |
| foundingDate is ISO 8601 | Critical |
| address has addressCountry | Warning |
| contactPoint has contactType | Critical |
| sameAs items are absolute https URLs | Critical |
| No duplicate Organization across pages | Warning |

## Battle-tested patterns

This skill is based on `netsujo.jp` Organization implementation:

- Emitted once in `app/layout.tsx`, never per-page (avoids entity duplication)
- `logo` and `image` both point to a 240x240px PNG with transparent background
- `sameAs` lists 5 canonical profiles (GitHub / X / LinkedIn / connpass / note) — all verified clickable, no logins
- `description` is 120 chars, Japanese, matches the `<meta name="description">` of `/about`
- `founder` references `飯田友広` with a URL back to `/about#founder` anchor
- ChatGPT search "Netsujo" returns the company description sourced directly from this JSON-LD (verified 2026-04)

The "emit once, in root layout" rule is enforced by the verify step which flags duplicate Organization nodes.

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / yaml |
| Schema version | 13.0 | Schema.org version target |
| inLanguage | ja | BCP-47 language tag for description |
| Strict mode | true | Fail on Warning level issues |
| Logo check | true | HEAD request to verify dimensions |

## Reference files

- `references/organization-schema-spec.md` — Full Schema.org Organization spec excerpts with examples
- `scripts/jsonld-organization.py` — Generator

## Related skills

- `netsujo-aio:jsonld-faqpage` — FAQPage JSON-LD (often paired with Organization on `/about` or `/faq`)
- `netsujo-aio:jsonld-article` — Article JSON-LD for blog/news (uses Organization as publisher)
- `netsujo-aio:jsonld-breadcrumb` — BreadcrumbList JSON-LD
- `claude-seo:seo-schema` — Comprehensive Schema.org validation (use for non-Organization types)
- `claude-seo:seo-geo` — AI citation readiness (Organization JSON-LD is the primary citation source)
