---
name: ga4-tracking-wiring
description: Wire GA4 event tracking (CTA clicks, outbound links, scroll depth, read completion) into a Next.js App Router project. Scaffolds a typed gtag wrapper, four event helpers, and four drop-in client components. Battle-tested on miyakodeit.com (PR #63 cta_click / first_guide_click / faq_expand) and netsujo.jp article pages (blog_view / scroll_depth_75 / read_complete / outbound_click). Use when user says "GA4 tracking", "wire gtag", "trackCTAClick", "scroll depth tracking", "outbound link tracking", or "read complete event".
---

# GA4 Tracking Wiring

Production-ready GA4 event wiring for Next.js App Router. Generates a typed `window.gtag` wrapper, four event helpers (`trackCTAClick` / `trackOutboundLink` / `trackScrollDepth` / `trackReadComplete`), and four client components that fire them at the right moment.

## What it does

1. **Generates a typed gtag wrapper** at `lib/analytics/ga4.ts` (SSR-safe, no-op when `window` undefined)
2. **Generates four event helpers** at `lib/analytics/events.ts` with strict TypeScript signatures
3. **Generates four client components** under `components/analytics/` (CTAButton, OutboundLink, ScrollDepthTracker, ReadCompleteTracker)
4. **Patches `app/layout.tsx`** to mount `<ScrollDepthTracker />` site-wide (optional, opt-out via flag)
5. **Protects existing files**: writes `.new` siblings and prints a merge guide when conflicts are detected

## When to use

- User says "GA4 tracking", "wire gtag", "trackCTAClick", "scroll depth", "outbound link tracking"
- New Next.js project that has `GA4_MEASUREMENT_ID` but no event helpers
- Standardizing tracking across Netsujo properties (miyakodeit / netsujo / soba-takahashi)
- Before launching a content site where read-through and CTA performance need measurement

## Events covered

| Helper | GA4 event name | Required params | Fires from |
|---|---|---|---|
| `trackCTAClick(label, position)` | `cta_click` | `event_label`, `cta_position` | `<CTAButton />` onClick |
| `trackOutboundLink(url, domain)` | `outbound_click` | `link_url`, `link_domain` | `<OutboundLink />` onClick |
| `trackScrollDepth(percent)` | `scroll_depth` | `percent_scrolled` (25/50/75/100) | `<ScrollDepthTracker />` IntersectionObserver |
| `trackReadComplete(articleSlug)` | `read_complete` | `article_slug` | `<ReadCompleteTracker />` 90% scroll + 30s dwell |

All four are mapped to GA4 custom dimensions registered by the `ga4-custom-dimensions` skill (recommended prerequisite, but not required to run this skill).

## Prerequisites

1. **GA4 measurement ID** (`G-XXXXXXXXXX`) available as `NEXT_PUBLIC_GA4_MEASUREMENT_ID`
2. **gtag.js loaded** in `app/layout.tsx` (the script will detect and skip if absent, but warn)
3. **Next.js 14+ App Router** (Pages Router not supported — use the `pages-router` branch of the template)
4. **TypeScript strict mode** recommended (the generated code assumes it)

Optional but recommended:
- `ga4-custom-dimensions` skill has run (12 dimensions registered including `event_label`, `cta_position`, `article_slug`)

## Usage

### Dry-run (default)

```bash
python3 scripts/ga4-tracking-wiring.py --target ./my-nextjs-app --dry-run
```

Output:

```
Plan:
  CREATE lib/analytics/ga4.ts
  CREATE lib/analytics/events.ts
  CREATE components/analytics/CTAButton.tsx
  CREATE components/analytics/OutboundLink.tsx
  CREATE components/analytics/ScrollDepthTracker.tsx
  CREATE components/analytics/ReadCompleteTracker.tsx
  UPDATE app/layout.tsx (add ScrollDepthTracker)
Existing files: 0 conflicts
```

### Apply

```bash
python3 scripts/ga4-tracking-wiring.py --target ./my-nextjs-app --apply
```

### Select a subset of events

```bash
python3 scripts/ga4-tracking-wiring.py --target ./my-nextjs-app --events cta,outbound --apply
```

Valid values: `cta`, `outbound`, `scroll`, `read`. Default is all four.

### Override measurement ID

```bash
python3 scripts/ga4-tracking-wiring.py \
  --target ./my-nextjs-app \
  --measurement-id G-XXXXXXXXXX \
  --apply
```

The ID is baked into the generated `ga4.ts` as a fallback when `process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID` is unset.

### Skip layout patch

```bash
python3 scripts/ga4-tracking-wiring.py --target ./my-nextjs-app --no-layout-patch --apply
```

Use when `app/layout.tsx` is heavily customized; you'll mount `<ScrollDepthTracker />` manually.

## Generated component examples

### CTAButton

```tsx
<CTAButton label="ヒーロー申込" position="hero" href="/contact">
  資料請求する
</CTAButton>
```

Fires `cta_click` with `event_label="ヒーロー申込"`, `cta_position="hero"`.

### OutboundLink

```tsx
<OutboundLink href="https://connpass.com/event/123/">
  connpassで申し込む
</OutboundLink>
```

Domain extracted automatically. Fires `outbound_click` with `link_url`, `link_domain="connpass.com"`.

### ScrollDepthTracker

```tsx
// app/layout.tsx (auto-patched)
<ScrollDepthTracker />
```

One instance site-wide. Fires `scroll_depth` once per threshold per page view (25 / 50 / 75 / 100%).

### ReadCompleteTracker

```tsx
// app/blog/[slug]/page.tsx
<ReadCompleteTracker articleSlug={params.slug} />
```

Fires `read_complete` when reader hits 90% scroll AND has spent 30+ seconds on page.

## Existing file protection

When a target file already exists, the script writes `<filename>.new` next to it and prints:

```
CONFLICT lib/analytics/events.ts
  Existing file kept. New version: lib/analytics/events.ts.new
  Merge guide: diff -u lib/analytics/events.ts lib/analytics/events.ts.new
```

`app/layout.tsx` is never overwritten — the script emits a patch snippet to stdout if it can't apply cleanly.

## Validation checks

| Check | Severity |
|---|---|
| Target is a Next.js App Router project (`app/` exists) | Critical |
| `NEXT_PUBLIC_GA4_MEASUREMENT_ID` set OR `--measurement-id` passed | Critical |
| Measurement ID matches `G-[A-Z0-9]{10}` pattern | Critical |
| `next` >= 14 in package.json | Warning |
| TypeScript strict mode enabled | Warning |
| `app/layout.tsx` contains gtag.js script tag | Warning |
| No conflicting `lib/analytics/` files | Info |

Critical issues abort apply. Warnings are printed but do not block.

## Battle-tested patterns

| 日付 | 案件 | 学び |
|---|---|---|
| 2026-05-24 | miyakodeit PR #63 `/study-group-kyoto` | 新規3イベント(connpass_cta_click / first_guide_click / faq_expand)を `cta_click` 1本に統合。`event_label` で分離する方が GA4 探索で柔軟 |
| 2026-05-27 | 飯田さん手動 GA4 設定 | カスタムディメンション「CTAラベル」(`event_label` パラメータ)を登録、探索でフィルタ「イベント名=cta_click」設定済 |
| 2026-05-28 | netsujo AI動画イベントレポート | 既存実装(`blog_view` / `scroll_depth_75` / `read_complete` / `outbound_click`)が新記事に自動適用された。`<ReadCompleteTracker articleSlug={slug} />` を記事テンプレに1行追加するだけ |

`cta_click`1本に絞る判断は重要。イベント名を増やすとGA4の24時間データ反映待ちが個別に発生するため、`event_label`分離が運用上有利。

## Configuration

| Setting | Default | Description |
|---|---|---|
| `--target` | `.` | Next.js project root |
| `--events` | `cta,outbound,scroll,read` | Comma-separated subset |
| `--measurement-id` | `process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID` | GA4 ID fallback |
| `--apply` | false | Write files (default is dry-run) |
| `--no-layout-patch` | false | Skip `app/layout.tsx` modification |
| `--scroll-thresholds` | `25,50,75,100` | Scroll depth breakpoints |
| `--read-complete-percent` | `90` | Scroll % for read_complete |
| `--read-complete-dwell-sec` | `30` | Min dwell time for read_complete |

## Reference files

- `references/tracking-events-catalog.md` — All 4 events with parameters, fire timing, GA4 explore configuration, Next.js App Router constraints, Consent Mode v2 notes, common mistakes
- `scripts/ga4-tracking-wiring.py` — Generator

## Related skills

- `netsujo-aio:ga4-custom-dimensions` — Register 12 custom dimensions in GA4 (prerequisite)
- `netsujo-aio:ga4-funnel-explore` — Build funnel explorations on the events this skill emits
- `claude-seo:seo-google` — GA4 organic traffic reporting via API
