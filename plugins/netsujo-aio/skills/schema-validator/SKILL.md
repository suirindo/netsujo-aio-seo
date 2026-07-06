---
name: schema-validator
description: Use when user says "schema validation", "JSON-LD check", "structured data", "rich results test", "schema.org valid", "graph integrity", when a build passes but structured data correctness is unverified, or BEFORE merging any PR that adds/modifies JSON-LD components (JsonLd component, dangerouslySetInnerHTML with application/ld+json).
---

# Schema Validator

Validates JSON-LD blocks against schema.org spec and Google Rich Results requirements, plus catches graph integrity issues (e.g., `Person.worksFor → Organization` where the Organization `@id` doesn't actually exist anywhere in the site's graph).

## Why this matters

Real incident on 2026-06-04: A new `CourseListJsonLd` component emitted Course schema with `provider: { '@type': 'CollegeOrUniversity', name: '公立はこだて未来大学' }` based on incorrect input data. The schema passed JSON.stringify validation, passed `npm run build`, and was deployed. Only manual fact-check by the owner caught it.

Even when the underlying facts are correct, JSON-LD failures (missing required fields, deprecated types post-update, broken `@id` references) silently degrade SEO and AI citation without any visible build error.

## What this skill checks

For each `<script type="application/ld+json">` block on the page:

### Structural validation
1. **Valid JSON** — parses cleanly
2. **`@context` present** — `https://schema.org`
3. **`@type` recognized** — valid schema.org type at current snapshot
4. **Required properties** — per Google Rich Results docs (e.g., Article requires headline/datePublished, Course requires name/provider, Event requires location/startDate)
5. **No deprecated types** — FAQPage rich result deprecated 2026-05-07 (still allowed for AI citation but warns); HowTo deprecated; etc.
6. **Property cardinality** — single vs. array correctness
7. **Reference resolution** — `@id` references within the page resolve to actual schema blocks (e.g., `Person.worksFor → Organization @id` must exist)

### Cross-block / cross-page integrity
8. **Organization `@id` uniqueness** — the canonical `${SITE_URL}/#organization` should be defined once and referenced elsewhere
9. **Person `@id` cross-references** — `/authors/{slug}#person` should appear consistently across the site
10. **BreadcrumbList consistency** — last item URL matches `mainEntityOfPage`
11. **Image references reachable** — `image` / `logo` URLs return 200 + image content-type
12. **Date format** — ISO 8601 (YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ)

### Google Rich Results-specific
13. **Article**: headline ≤ 110 chars, image ≥ 1200px wide, author present
14. **Course**: provider Address present (else Course warning in Rich Results Test)
15. **Event**: endDate ≥ startDate, location present
16. **Product / SoftwareApplication**: offers OR aggregateRating required for SERP eligibility

## What this skill does

1. **Discover JSON-LD blocks** via:
   - Static analysis: grep `JsonLd` components in changed files + their emitted schema shape
   - Live page: fetch URL, parse HTML, extract all `<script type="application/ld+json">`
2. **For each block, validate** against rules above
3. **For multi-block pages**, check cross-block integrity (e.g., Person.worksFor → Organization @id resolution)
4. **For Google Rich Results-eligible types**, optionally call Google's Rich Results Test API if available, else apply local rules from public Google docs
5. **Report** per-block PASS/WARN/FAIL with exact location and suggested fix

## Critical rules (enforced)

- **safeJsonLd() wrapper required** for `dangerouslySetInnerHTML` — `</script>` escape must be applied. Detect bare `JSON.stringify` without escape
- **No optional chaining without fallback** for required schema fields — `description: post?.excerpt` が `undefined` になると `JSON.stringify` はそのキーごと**黙って省略**し、必須フィールドがエラーなしで欠落する
- **Date strings must be ISO 8601** — `2024.05.14` is not valid; `2024-05-14` is
- **CourseInstance.location required** when emitting Course schema
- **Use `schema:` URL prefix** for property names in `@type` (auto-handled by schema.org context but warn on legacy patterns)

## Patterns specifically flagged

- `@type: 'FAQPage'` without comment noting "for AI citation" (post 2026-05-07 deprecation)
- `Person` with no `worksFor` + no `affiliation` + no `memberOf` — weak entity graph
- `Organization` with `address` but missing `addressCountry`
- `image` field as relative URL (must be absolute)
- `keywords` as space-separated single string (should be comma-separated)
- `sameAs` array with mixed protocols (http vs https) or duplicate entries

## Usage

### Pattern 1: PR pre-merge schema check

```
> PR #109 の追加された Course schema を schema-validator で検証
```

### Pattern 2: Production page schema audit

```
> /authors/iida-tomohiro の全 JSON-LD を schema-validator
```

### Pattern 3: Cross-site graph integrity

```
> netsujo.jp 全ページの Organization @id 一貫性を確認
```

## Output

```
{
  "url_or_diff": "PR #109 src/components/seo/json-ld.tsx",
  "blocks_validated": 8,
  "passes": 7,
  "warnings": [
    {
      "block": "FaqPageJsonLd at home",
      "warning": "Rich Results deprecated 2026-05-07. Schema valid for AI citation only.",
      "verdict": "keep, but document role"
    }
  ],
  "failures": [
    {
      "block": "CourseListJsonLd",
      "field": "hasCourseInstance.location",
      "verdict": "Required field present but provider name '公立はこだて未来大学' likely fabricated (verified via content-fact-validator)",
      "fix": "Cross-reference with Strapi article before keeping"
    }
  ]
}
```

## References

- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema.org Latest: https://schema.org/version/latest/schemaorg-current-https.jsonld
- 2026-05-07 FAQ Rich Results deprecation: developers.google.com/search/blog/2026/05/faq
