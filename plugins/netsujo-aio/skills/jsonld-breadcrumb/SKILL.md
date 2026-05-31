---
name: jsonld-breadcrumb
description: Generate and validate BreadcrumbList JSON-LD structured data for Next.js App Router, Strapi, and static sites. Auto-derives breadcrumb trails from URL pathnames via a label dictionary, outputs drop-in React components using usePathname(), and enforces Google rich results requirements (sequential position, absolute item URLs, omitted last-item URL). Battle-tested on miyakodeit.com `/study-group-kyoto` (PR #63) and netsujo.jp全ページ. Use when user says "breadcrumb schema", "BreadcrumbList JSON-LD", "breadcrumb structured data", "breadcrumb rich result", "パンくず schema", "breadcrumb markup", or has dynamic `[slug]` segments that need a generated breadcrumb trail.
---

# BreadcrumbList JSON-LD Generator

Production-ready BreadcrumbList JSON-LD with React component output for the Next.js App Router, automatic path-to-label resolution, and Google Rich Results Test compatibility.

## What it does

1. **Generates valid BreadcrumbList JSON-LD** from a URL pathname plus a YAML label dictionary
2. **Emits Next.js App Router React components** that resolve breadcrumbs at runtime via `usePathname()`
3. **Handles dynamic segments** (`[slug]`, `[id]`) by accepting a runtime title prop or frontmatter lookup
4. **Validates against Schema.org BreadcrumbList spec**: sequential `position`, absolute item URLs, last-item URL omission
5. **Scans an `app/` tree** to enumerate all routes and generate a single `BreadcrumbSchema.tsx` covering them

## When to use

- User says "breadcrumb schema", "BreadcrumbList JSON-LD", "breadcrumb rich result"
- Adding a new section under an existing tree (`/blog/[slug]`, `/events/[id]`)
- Migrating to App Router and re-implementing breadcrumbs
- Before Google Rich Results Test submission for non-home pages

## Critical Google constraints

Per [Google BreadcrumbList guidelines](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb):

1. **`position` starts at 1 and increments by exactly 1** — gaps or duplicates invalidate the markup
2. **`item` must be an absolute URL** (`https://example.com/blog`), not a relative path
3. **The last `ListItem` MAY omit `item`** since it represents the current page
4. **`name` should match the visible breadcrumb label** on the page
5. **Multiple breadcrumb trails** are allowed (e.g. `Books > Science > Astronomy` and `Science > Astronomy`) but each must be a separate `BreadcrumbList`

This skill enforces all 5 at generation time.

## Usage

### Generate JSON-LD from a single path

```bash
python3 scripts/jsonld-breadcrumb.py \
  --path /blog/ai-blockchain-enterprise \
  --config breadcrumb-config.yaml \
  --site https://netsujo.jp \
  --output schema.json
```

YAML config format:

```yaml
site: https://netsujo.jp
inLanguage: ja
labels:
  /: ホーム
  /blog: ブログ
  /blog/[slug]: "{title}"   # resolved from frontmatter or runtime prop
  /events: イベント
  /events/[id]: "{title}"
  /company: 会社概要
  /contact: お問い合わせ
```

Output (`schema.json`):

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "inLanguage": "ja",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://netsujo.jp/" },
    { "@type": "ListItem", "position": 2, "name": "ブログ", "item": "https://netsujo.jp/blog" },
    { "@type": "ListItem", "position": 3, "name": "AI×ブロックチェーンが企業にもたらす変革" }
  ]
}
```

Note: the last `ListItem` omits `item` per Google guidance.

### Generate React component (Next.js App Router)

```bash
python3 scripts/jsonld-breadcrumb.py \
  --config breadcrumb-config.yaml \
  --format react \
  --output components/schema/BreadcrumbSchema.tsx
```

Output:

```tsx
"use client";
import { usePathname } from "next/navigation";
import Script from "next/script";

const SITE = "https://netsujo.jp";
const LABELS: Record<string, string> = {
  "/": "ホーム",
  "/blog": "ブログ",
  "/events": "イベント",
  "/company": "会社概要",
};

export function BreadcrumbSchema({ title }: { title?: string }) {
  const pathname = usePathname();
  // ... resolves segments to labels, emits BreadcrumbList JSON-LD
}
```

Drop it into a `layout.tsx` and pass `title` from each leaf page.

**XSS hardening**: the emitted component escapes `<`, `>`, `&`, U+2028, U+2029 in the inline JSON-LD before injection via `dangerouslySetInnerHTML`. This is the OWASP-recommended pattern for inline JSON in HTML and neutralises malicious titles containing `</script>` or other HTML-breaking content. Re-running the generator overwrites the file, so do not hand-edit the escape block.

### Scan an `app/` tree

```bash
python3 scripts/jsonld-breadcrumb.py \
  --scan ./app/ \
  --config breadcrumb-config.yaml \
  --output components/schema/BreadcrumbSchema.tsx
```

Walks every `page.tsx` under `app/`, extracts segments (including `[slug]`, `(group)`, `@parallel`), and warns when a route is missing from the label dictionary.

### Dynamic segment resolution

For `/blog/[slug]`, pass the resolved title at render time:

```tsx
// app/blog/[slug]/page.tsx
import { BreadcrumbSchema } from "@/components/schema/BreadcrumbSchema";

export default async function Page({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  return (
    <>
      <BreadcrumbSchema title={post.title} />
      {/* ... */}
    </>
  );
}
```

The skill never guesses the title — passing it explicitly avoids the `position` corruption bug observed when a dynamic segment is treated as a literal `[slug]` label.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type=BreadcrumbList, itemListElement | Critical |
| itemListElement not empty | Critical |
| Each item: @type=ListItem, position, name | Critical |
| position is 1-indexed and strictly increasing by 1 | Critical |
| item URLs are absolute (https://) when present | Critical |
| Last ListItem MAY omit item (recommended) | Warning |
| name length 1-128 chars | Warning |
| inLanguage is BCP-47 | Warning |

## Battle-tested patterns

This skill is based on production implementations:

- **2026-05-24 PR #63でmiyakodeit.com `/study-group-kyoto`にBreadcrumbList JSON-LDを実装**。Google Search ConsoleのBreadcrumb rich resultレポートで取得を確認
- **netsujo.jp全ページ**で同パターン適用。`/blog/[slug]`, `/events/[id]`の動的セグメントでpositionが崩れる事故を、`title` propの明示的な受け渡しで防止
- **動的`[slug]`をliteral labelとして埋めてしまうバグ事例** — 過去に`name: "[slug]"`のまま出してしまった事故あり。本skillはdynamic segmentを検知してruntime resolutionを強制

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / yaml |
| Schema version | 13.0 | Schema.org version target |
| inLanguage | ja | BCP-47 language tag |
| Omit last item URL | true | Recommended by Google |
| Trailing slash on home | true | `/` resolved to `https://site/` |
| Strict mode | true | Fail on Warning level issues |

## Reference files

- `references/breadcrumb-schema-spec.md` — Full Schema.org spec excerpts, position rules, App Router segment semantics, common mistakes
- `scripts/jsonld-breadcrumb.py` — Generator (CLI + React component emitter)

## Related skills

- `netsujo-aio:jsonld-faqpage` — FAQPage JSON-LD (often paired on the same page)
- `netsujo-aio:jsonld-article` — Article JSON-LD for blog/news
- `netsujo-aio:jsonld-organization` — Organization JSON-LD (sitewide root)
- `claude-seo:seo-schema` — Comprehensive Schema.org validation across types
