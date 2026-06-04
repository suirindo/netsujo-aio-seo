---
name: link-integrity-tester
description: Crawl a site or PR Preview URL and verify every internal link resolves to an existing route. Detects broken anchors, redirect chains, semantic mismatches (e.g. button labeled "all articles" pointing to event archive), and dead OG image references. Use when user says "test links", "link check", "link integrity", "broken link", "全リンク確認", "リンク切れ", "click test", or BEFORE merging any PR that changes navigation/CTA buttons. Triggered by the lessons learned from 2026-06-04 /blog button mislinking to /archive instead of all-articles page.
---

# Link Integrity Tester

Crawls a site (or a single Pull Request's Preview URL) and verifies every internal link points to an existing, semantically-aligned destination. Catches the kind of mismatch where `<Link href="/archive">全62記事を一覧で見る</Link>` reads as "view all 62 articles" but actually shows event archive (158 events).

## Why this matters

Real incident on 2026-06-04: A button labeled "全62記事を一覧で見る" linked to `/archive` (event history page with 158 events), not a blog post listing page. Build passed, visual UI looked fine, but the destination didn't match the button's promise. User reported the issue.

Static analysis (`grep`/`tsc`) catches non-existent routes but **never catches semantic link mismatches**. A link that compiles is not necessarily a link that fulfills the user's expectation.

## What this skill checks

For each `<Link href="...">` or `<a href="...">` in the changed files (or whole site):

1. **Route exists** — destination resolves to an actual page (not 404)
2. **Anchor exists** — if `#hash` is present, target element with that id exists
3. **Semantic alignment** — link text claims X items / pages / records, destination actually has X
4. **Redirect chain depth** — destination redirects ≤ 1 hop (not chained redirects)
5. **Cross-domain integrity** — external links return 2xx (or 401 for known SSO-protected)
6. **OG image reachable** — `<meta property="og:image">` URL returns 200 + image content-type
7. **No duplicate / conflicting routes** — same path declared in multiple places

## Critical patterns enforced

- "全X記事" / "全X件" / "Xの一覧" labels → destination must have ≥ X visible items
- "戻る" / "一覧へ" labels → destination must be parent-route, not sibling
- "詳しく見る" labels → destination must be specific detail page, not category index
- "カテゴリで探す" labels → destination must be category index (`/category`), not single category (`/category/foo`)
- "全 N 記事" + dynamic N → destination contains list of length matching N (within ±1 tolerance for content filter)

## What this skill does

1. **Discover changed routes/links** via `git diff` (when run on a PR) or sitemap walk (when run on a site)
2. **For each link**:
   - Fetch destination (HEAD then GET if needed)
   - Extract semantic expectation from link text via regex (`/全(\d+)記事/`, `/(\d+)件/`, etc.)
   - Compare against destination's actual content
3. **For each OG image**:
   - Verify URL returns 200 + `image/*` content-type
   - Verify dimensions match declared `og:image:width/height` (if present)
4. **Generate report** — pass/fail per link, with diff between expected and actual

## Usage

### Pattern 1: Run on a PR before merge

```
> PR #83 の全変更箇所のリンクを link-integrity-tester で検証
```

Walks `git diff main` to find changed files containing href, fetches Preview URL,
clicks/follows each link, returns pass/fail per link.

### Pattern 2: Run on production after deploy

```
> netsujo.jp の全リンクを link-integrity-tester で全件確認
```

Walks sitemap.xml, follows every internal link, returns broken/mismatched ones.

### Pattern 3: Per-page focused check

```
> /blog 単体ページのリンクを全件 link-integrity-tester
```

## Critical rules (enforced)

- **Build passes ≠ links work**. tsc only checks route file existence, not semantic intent. This skill verifies intent
- **Run BEFORE merge whenever <Link href>, <a href>, button onClick href, redirect rule changes**
- **Run AFTER deploy** when ISR/CDN cache might have shifted route resolution
- For Vercel Preview URLs behind SSO, fall back to "build the page text + static analysis" mode

## Output

```
{
  "site": "PR #83 Preview",
  "links_checked": 47,
  "passes": 41,
  "failures": [
    {
      "from": "/blog",
      "anchor_text": "全62記事を一覧で見る",
      "href": "/archive",
      "verdict": "semantic_mismatch",
      "expected": "blog post list of ~62 items",
      "actual": "/archive shows allEventsHistory (158 events), not blog posts",
      "suggested_fix": "Change href to /blog/all (newly created)"
    }
  ],
  "og_image_failures": [],
  "duration_ms": 12430
}
```

## References

- 2026-06-04 lessons-learned: `/blog/全62記事を一覧で見る` → `/archive` mislink incident
- Vercel preview URL pattern: `https://{project}-git-{branch-slug}-{org}.vercel.app`
