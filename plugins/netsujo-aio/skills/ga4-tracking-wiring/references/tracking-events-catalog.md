# GA4 Tracking Events Catalog

Reference for all four events emitted by the `ga4-tracking-wiring` skill. Use this when configuring GA4 explorations, debugging missing events, or extending the event surface.

## Event 1: `cta_click`

Fired from `<CTAButton />` onClick handler.

| Parameter | Type | Required | Example | Notes |
|---|---|---|---|---|
| `event_label` | string | yes | `"ヒーロー申込"` | Human-readable label shown in GA4 explore. Registered as custom dimension "CTAラベル" |
| `cta_position` | string | yes | `"hero"`, `"footer"`, `"sidebar"` | Page region. Use a small fixed vocabulary |
| `value` | number | no | `1` | Conversion value if monetary |

**Fire timing**: Synchronous in onClick before navigation. The wrapper uses `gtag('event', ..., { event_callback })` so navigation is not blocked beyond 500ms.

**GA4 explore setup**:
1. Explore > Free form
2. Dimensions: `event_label`, `cta_position`
3. Metrics: `event_count`, `total_users`
4. Filter: `event_name = cta_click`

**Common mistake**: Defining one event per CTA (`hero_cta_click`, `footer_cta_click`, ...). GA4 has a 24-hour propagation delay per new event name. Always use `cta_click` + `event_label`.

## Event 2: `outbound_click`

Fired from `<OutboundLink />` onClick handler when `href` hostname differs from `window.location.hostname`.

| Parameter | Type | Required | Example | Notes |
|---|---|---|---|---|
| `link_url` | string | yes | `"https://connpass.com/event/123/"` | Full URL |
| `link_domain` | string | yes | `"connpass.com"` | Auto-extracted via `new URL(href).hostname` |
| `link_text` | string | no | `"connpassで申し込む"` | Anchor text. Auto-captured when `children` is a plain string |

**Fire timing**: onClick, before navigation. `target="_blank"` is auto-added with `rel="noopener noreferrer"`.

**GA4 explore setup**:
- Path exploration starting from `outbound_click` to see what users do before/after leaving
- Aggregate by `link_domain` to find top partner sites

**Common mistake**: Calling `trackOutboundLink` on internal links. The component skips internal hostnames automatically; if you call the helper directly, validate hostname first.

## Event 3: `scroll_depth`

Fired from `<ScrollDepthTracker />` (one instance in `app/layout.tsx`). Uses sentinel `<div>` elements positioned at 25/50/75/100% of `document.documentElement.scrollHeight` and observed via IntersectionObserver.

| Parameter | Type | Required | Example | Notes |
|---|---|---|---|---|
| `percent_scrolled` | number | yes | `25`, `50`, `75`, `100` | Discrete threshold |

**Fire timing**: When the sentinel enters viewport. Each threshold fires at most once per page view (tracked in a `Set` keyed on `pathname`).

**GA4 explore setup**:
- Funnel: `page_view` -> `scroll_depth(75)` -> `read_complete`
- Compare scroll-to-75 rate across `page_location`

**Common mistake**: Re-mounting the tracker on each route change. The component uses `usePathname()` to reset its internal `Set` and re-attach observers when the path changes.

## Event 4: `read_complete`

Fired from `<ReadCompleteTracker articleSlug={slug} />`. Triggers when BOTH conditions are met:

1. User scrolled past 90% of article container
2. Dwell time on page >= 30 seconds

| Parameter | Type | Required | Example | Notes |
|---|---|---|---|---|
| `article_slug` | string | yes | `"ai-blockchain-2026"` | Maps to `article_slug` custom dimension |
| `dwell_sec` | number | no | `47` | Actual dwell time at fire moment |

**Fire timing**: Whichever condition is satisfied second triggers the event. Fires at most once per page view per slug.

**GA4 explore setup**:
- Read-through rate = `read_complete` events / `blog_view` events grouped by `article_slug`
- Cohort: users with `read_complete >= 3` are highly engaged

**Common mistake**: Firing on 100% scroll without dwell guard. Bots and accidental skim-scrolls inflate the metric. Always require both conditions.

## Next.js App Router constraints

All four components are `"use client"`. Important rules:

1. **No SSR access to `window`** — the `gtag` wrapper guards with `typeof window === "undefined"` early return
2. **No call during render** — only call helpers in event handlers or `useEffect`
3. **Hydration safety** — the trackers render `null` and only attach listeners in `useEffect`, so they never cause hydration mismatches
4. **Streaming compatibility** — works with React Server Components; the trackers are leaves in the client island

If `app/layout.tsx` is a server component (default), import the client tracker at the top and render it as a child — it will hydrate independently.

## Consent Mode v2

When the project uses Consent Mode v2 (EEA / UK requirement):

1. `gtag('consent', 'default', {...})` is set in `app/layout.tsx` before the GA4 config
2. Until consent is granted, gtag buffers events
3. The wrapper this skill generates does NOT short-circuit on missing consent — it lets gtag handle buffering / dropping per consent state
4. If you need strict opt-in (no buffering), pass `--consent-strict` (writes a `hasConsent()` guard into `ga4.ts`)

## Common mistakes summary

| Mistake | Symptom | Fix |
|---|---|---|
| Calling `gtag` in SSR | `ReferenceError: window is not defined` | Use the wrapper, never `window.gtag` directly |
| Missing `event_label` | Events grouped as "(not set)" in explore | Always pass label for `cta_click` |
| One event per CTA | 24h propagation delay multiplied | Use `event_label` to split, not event name |
| Tracking internal links as outbound | Inflated outbound count | Use `<OutboundLink />` which auto-detects |
| Read complete on 100% scroll only | Bots inflate metric | Require dwell guard (this skill enforces) |
| Re-firing scroll thresholds | `scroll_depth(50)` fires 10x per page | Use the per-pathname `Set` (this skill enforces) |
| Forgetting `"use client"` | Build error: "Event handlers cannot be passed to Client Component props" | All four components include the directive |
| Registering custom dimensions after events fire | Dimension shows "(not set)" for historical data | Run `ga4-custom-dimensions` skill BEFORE this one |

## Verification after apply

1. `npm run dev`, open DevTools > Network, filter `collect?v=2`
2. Click a `<CTAButton />` — should see request with `en=cta_click&ep.event_label=...`
3. Scroll to 25/50/75/100 — should see four `en=scroll_depth` requests
4. Open an article, scroll past 90%, wait 30s — should see `en=read_complete`
5. Click an external link — should see `en=outbound_click&ep.link_domain=...`
6. GA4 > Realtime > Event count by Event name (24h delay before showing in standard reports)
