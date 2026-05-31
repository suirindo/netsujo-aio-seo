---
name: jsonld-event
description: Generate and validate Schema.org Event JSON-LD structured data for online, offline, and hybrid events. Supports OnlineEventAttendanceMode / OfflineEventAttendanceMode / MixedEventAttendanceMode, Google rich results requirements (timezone-aware startDate, 1920x1080 image), and outputs JSON / Next.js React component / Strapi v5 component. Battle-tested on miyakodeit.com (155+京都IT勉強会イベント) and used for Google Meet online meetups, Kyoto offline venues, and hybrid sessions. Use when user says "Event schema", "Event JSON-LD", "event structured data", "rich results event", "online event schema", "offline event schema", "hybrid event schema", "MixedEventAttendanceMode", "connpass schema", or has event listing pages that need rich results eligibility.
---

# Event JSON-LD Generator

Production-ready Event JSON-LD with online / offline / hybrid attendance modes, React component output, Strapi v5 component scaffolding, and Google Rich Results compatibility checks.

## What it does

1. **Generates valid Event JSON-LD** from a YAML / JSON event description
2. **Switches attendance mode** between `OnlineEventAttendanceMode`, `OfflineEventAttendanceMode`, and `MixedEventAttendanceMode` via `--attendance`
3. **Enforces Google rich results requirements**: timezone-aware `startDate`, `location` shape per mode, recommended 1920x1080 hero image
4. **Validates against Schema.org Event spec**: required fields, allowed `eventStatus` values, `offers` structure
5. **Outputs three formats**: plain JSON, Next.js App Router React component, Strapi v5 component scaffold
6. **Batch mode** for generating JSON-LD for a directory of events (e.g. connpass export, miyakodeit イベントアーカイブ)

## When to use

- User says "Event schema", "Event JSON-LD", "event structured data", "rich results event"
- Adding event listing or single-event pages to a Next.js / Strapi site
- After importing connpass / Peatix / Doorkeeper events into a CMS
- Before submitting an event page to Google Rich Results Test
- Migrating from generic JSON-LD to attendance-mode-aware structure (post-COVID Google requirement)

## Critical Google constraints

Per [Google Event structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/event):

1. **`startDate` MUST include a timezone offset** (e.g. `2026-05-28T19:00:00+09:00`). Naive datetimes are rejected by rich results.
2. **`location` shape depends on attendance mode**:
   - Online → `VirtualLocation` with `url`
   - Offline → `Place` with `address` (PostalAddress)
   - Mixed → array of both
3. **OfflineEvent MUST NOT have a `url` on its location** — `url` belongs to `VirtualLocation` only
4. **`eventAttendanceMode` is required when not purely offline** — omitting it on a hybrid event loses the online half of the rich result
5. **Hero image should be 1920x1080** (16:9) and at least 1200px wide for rich results eligibility
6. **`eventStatus` defaults to `EventScheduled`** — explicitly set `EventCancelled`, `EventPostponed`, or `EventRescheduled` when applicable, otherwise stale events keep showing as scheduled

This skill enforces all 6 at generation time.

## Usage

### Generate JSON-LD only

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --output schema.json
```

YAML format:

```yaml
name: AI動画制作ハンズオン勉強会
startDate: "2026-05-28T19:00:00+09:00"
endDate: "2026-05-28T21:00:00+09:00"
description: ChatGPT と Runway を使った AI 動画制作のハンズオン勉強会です。
image: https://miyakodeit.com/events/2026-05-28-ai-video/hero.jpg
attendance: online
location:
  url: https://meet.google.com/abc-defg-hij
  name: Google Meet
organizer:
  name: みやこでIT
  url: https://miyakodeit.com
offers:
  price: "0"
  priceCurrency: JPY
  availability: InStock
  url: https://miyakodeit.connpass.com/event/123456/
eventStatus: EventScheduled
```

### Online event (OnlineEventAttendanceMode)

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --attendance online \
  --output schema.json
```

Produces `eventAttendanceMode: "https://schema.org/OnlineEventAttendanceMode"` and a `VirtualLocation` with `url`.

### Offline event (OfflineEventAttendanceMode)

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --attendance offline \
  --output schema.json
```

Produces `eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode"` and a `Place` with `address`. Used for 京都オフライン会場イベント.

### Hybrid event (MixedEventAttendanceMode)

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --attendance mixed \
  --output schema.json
```

Produces `eventAttendanceMode: "https://schema.org/MixedEventAttendanceMode"` and `location` as an array of `[VirtualLocation, Place]`.

### Next.js React component output

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --attendance online \
  --output components/event/EventSchema.tsx \
  --format react
```

Output:

```tsx
import Script from "next/script"

export function EventSchema() {
  return (
    <Script
      id="event-schema"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Event",
          name: "...",
          startDate: "...",
          eventAttendanceMode: "https://schema.org/OnlineEventAttendanceMode",
          location: { "@type": "VirtualLocation", url: "..." },
          // ...
        }),
      }}
    />
  )
}
```

### Strapi v5 component scaffold

```bash
python3 scripts/jsonld-event.py \
  --input event.yaml \
  --output src/components/event/schema.json \
  --format strapi
```

Generates a Strapi v5 component JSON definition (`category: event`, fields aligned with Schema.org Event) so the structured data can be authored in the Strapi admin and consumed by the frontend.

### Batch mode

```bash
python3 scripts/jsonld-event.py \
  --batch ./events/ \
  --output ./public/jsonld/
```

Reads every `*.yaml` / `*.json` under `./events/` and writes one JSON-LD file per event. Used to backfill 155+miyakodeitイベントアーカイブ.

### connpass URL extraction (planned)

```bash
python3 scripts/jsonld-event.py \
  --connpass-url https://miyakodeit.connpass.com/event/123456/ \
  --output schema.json
```

Future: scrape title / start / end / venue / capacity / fee from a connpass event page and emit Event JSON-LD. Currently spec only — implementation deferred.

## Schema validation

Built-in checks before output:

| Check | Severity |
|---|---|
| Required: @context, @type=Event, name, startDate, location | Critical |
| startDate has timezone offset | Critical |
| endDate >= startDate when both present | Warning |
| location shape matches eventAttendanceMode | Critical |
| OfflineEvent location has no `url` field | Critical |
| Online location has `url` | Critical |
| Offline location has `address.addressCountry` | Warning |
| eventStatus in allowed set | Critical |
| image present and >= 1200px wide (heuristic) | Warning |
| offers.price and offers.priceCurrency both set or both absent | Critical |
| organizer.name present | Warning |

## Battle-tested patterns

This skill is based on `miyakodeit.com` event implementation:

- 155+京都IT勉強会イベントアーカイブ(2022〜2026)で稼働中
- `OnlineEventAttendanceMode`:Google Meet / Zoomオンライン勉強会
- `OfflineEventAttendanceMode`:京都市内オフライン会場(京都リサーチパーク、CAMPHOR-、QUESTIONなど)
- `MixedEventAttendanceMode`:ハイブリッド開催(会場+配信)
- 2026-05-28 AI動画制作ハンズオン(`/blog/ai-video-introduction-2026-05-28`、Google Meet開催、参加18名)で`OnlineEventAttendanceMode` JSON-LDを実装。後日ChatGPTで「京都AI動画イベント」検索時にcitationを確認

## Configuration

| Setting | Default | Description |
|---|---|---|
| Output format | json | json / react / strapi |
| Attendance mode | offline | online / offline / mixed |
| Schema version | 13.0 | Schema.org version target |
| Default timezone | +09:00 | Used only as warning anchor; never auto-injected |
| Strict mode | true | Fail on Warning level issues |
| Default eventStatus | EventScheduled | Override via input or `--status` |

## Reference files

- `references/event-schema-spec.md` — Schema.org Event spec excerpts: required/recommended fields, three attendance modes, `Place` vs `VirtualLocation`, `eventStatus` values, common mistakes
- `scripts/jsonld-event.py` — Generator

## Related skills

- `netsujo-aio:jsonld-faqpage` — FAQPage JSON-LD (often paired on event detail pages)
- `netsujo-aio:jsonld-organization` — Organization JSON-LD for the `organizer` field
- `netsujo-aio:jsonld-article` — Article JSON-LD for event report blog posts
- `netsujo-aio:jsonld-breadcrumb` — BreadcrumbList JSON-LD for `/events/[slug]` pages
- `claude-seo:seo-schema` — Comprehensive Schema.org validation (use for non-Event types)
