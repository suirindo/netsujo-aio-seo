# BreadcrumbList Schema Spec Reference

Reference excerpts and pitfalls for Schema.org `BreadcrumbList` JSON-LD, focused on Google Rich Results eligibility and Next.js App Router integration.

## Required fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `@context` | string | yes | Always `https://schema.org` |
| `@type` | string | yes | Always `BreadcrumbList` |
| `itemListElement` | `ListItem[]` | yes | Ordered array of trail items |
| `inLanguage` | BCP-47 string | recommended | e.g. `ja`, `en-US` — helps multilingual rich results |

Each `ListItem` requires:

| Field | Type | Required | Notes |
|---|---|---|---|
| `@type` | string | yes | Always `ListItem` |
| `position` | integer | yes | 1-indexed, strictly increasing by 1 |
| `name` | string | yes | Visible label (max 128 chars practical) |
| `item` | URL | conditional | Absolute URL. MAY be omitted on the last item (current page) |

## Position rule (most common bug)

Per Google: `position` "must start at 1 and increment by exactly 1". Common failures:

- Starting at 0 (`position: 0` for home)
- Skipping a position (`1, 2, 4`) when a route group `(marketing)` was accidentally treated as a URL segment
- Duplicating a position (`1, 2, 2, 3`) when a parallel route slot `@modal` slipped through

This skill strips App Router `(group)` and `@parallel` segments before numbering.

## Absolute vs relative URLs

Google requires `item` to be an absolute URL when present:

- OK: `"item": "https://netsujo.jp/blog"`
- NG: `"item": "/blog"` — invalidates the markup

Always pass `site` (origin) to the generator. The skill rejects relative URLs at validation time.

## Last-item URL omission

Google explicitly allows omitting `item` on the final `ListItem` since it represents the current page. Recommended for two reasons:

1. Prevents self-canonical confusion in some crawlers
2. Matches the visible breadcrumb pattern (last crumb is usually unlinked)

This skill omits the last `item` by default; override with `--no-omit-last-url` if your design links the current page.

## App Router segment semantics

Next.js App Router introduces non-URL segments that must NOT appear in the breadcrumb:

| Segment pattern | URL impact | Breadcrumb impact |
|---|---|---|
| `app/blog/page.tsx` | `/blog` | included |
| `app/(marketing)/about/page.tsx` | `/about` | `(marketing)` skipped |
| `app/@modal/login/page.tsx` | `/login` (parallel slot) | `@modal` skipped |
| `app/blog/[slug]/page.tsx` | `/blog/:slug` | dynamic — needs runtime title |
| `app/shop/[...path]/page.tsx` | catch-all | flatten or break into multiple crumbs |

The scanner (`--scan ./app/`) handles `(group)` and `@parallel` correctly. Dynamic segments are kept as-is in the dictionary key (`/blog/[slug]`) and resolved at runtime via the `title` prop.

## Dynamic [slug] handling — the bug to avoid

Naive implementations have produced markup like:

```json
{ "position": 3, "name": "[slug]", "item": "https://example.com/blog/[slug]" }
```

This is the leading cause of failed Rich Results validation for App Router sites. The fix is to:

1. Keep `[slug]` only as a dictionary key, never as an emitted label
2. Require a runtime `title` prop on the leaf page
3. Fail loudly if a dynamic segment is asked to render without a title

This skill enforces (3) — generator raises an error rather than emit `[slug]` as a label.

## Multiple breadcrumb trails

A page that lives under two hierarchies (e.g. `Books > Astronomy > Black Holes` AND `Science > Astronomy > Black Holes`) can emit two separate `BreadcrumbList` objects on the same page. They MUST be separate JSON-LD blocks, not merged. Most sites do not need this; emit one trail per page.

## inLanguage and i18n

For multilingual sites:

- Set `inLanguage: ja` on Japanese pages
- Set `inLanguage: en-US` on English pages
- The label dictionary should be language-specific (separate config files per locale)

For Next.js i18n routing (`/ja/blog`, `/en/blog`), the first segment becomes the locale crumb — usually skip it or rename via the dictionary (`/ja: 日本語`, `/en: English`).

## Common mistakes checklist

| Mistake | Detection |
|---|---|
| `position` starts at 0 | validator CRITICAL |
| `position` skips or duplicates | validator CRITICAL |
| `item` is relative path | validator CRITICAL |
| `name: "[slug]"` literal | generator raises error |
| Route group `(marketing)` in URL | scanner strips before emission |
| Last item has stale URL of previous page | use `--omit-last-url` (default) |
| Missing `@context` | validator CRITICAL |
| Trailing slash inconsistency | `normalize_path()` strips trailing slash except root |
| Home crumb missing | always emitted at position 1 |
| Mixed casing in URL (`/Blog` vs `/blog`) | crawlers may treat as different pages — pick one |

## Testing

Validate output with:

1. [Google Rich Results Test](https://search.google.com/test/rich-results) — pastes JSON-LD or fetches a URL
2. [Schema Markup Validator](https://validator.schema.org/) — broader Schema.org coverage
3. Google Search Console > Enhancements > Breadcrumbs — production-side validation after deploy

## References

- [Google: BreadcrumbList structured data](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)
- [Schema.org BreadcrumbList](https://schema.org/BreadcrumbList)
- [Schema.org ListItem](https://schema.org/ListItem)
- [Next.js App Router file conventions](https://nextjs.org/docs/app/api-reference/file-conventions)
