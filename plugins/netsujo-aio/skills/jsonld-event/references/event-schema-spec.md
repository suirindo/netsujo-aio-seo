# Schema.org Event Spec (excerpt for JSON-LD generation)

Reference distilled from [schema.org/Event](https://schema.org/Event) and [Google Event structured data guidelines](https://developers.google.com/search/docs/appearance/structured-data/event).

## Required fields

| Field | Type | Notes |
|---|---|---|
| `@context` | string | Always `"https://schema.org"` |
| `@type` | string | Always `"Event"` (or a subtype like `BusinessEvent`, `EducationEvent`) |
| `name` | string | Event title |
| `startDate` | ISO 8601 datetime | **MUST include timezone offset** (e.g. `2026-05-28T19:00:00+09:00`). Naive datetimes are rejected by Google rich results. |
| `location` | VirtualLocation / Place / array | Shape depends on `eventAttendanceMode` (see below) |

## Recommended fields

| Field | Type | Notes |
|---|---|---|
| `endDate` | ISO 8601 datetime | Must be >= startDate. Include timezone offset. |
| `description` | string | Plain text or limited HTML. 50-1500 chars recommended. |
| `image` | URL or ImageObject | 1920x1080 (16:9) preferred. Minimum 1200px wide for rich results eligibility. |
| `organizer` | Organization / Person | Provide at least `name`. `url` recommended. |
| `performer` | Person / Organization | Speaker / band / instructor. Single or array. |
| `eventStatus` | EventStatusType | See allowed values below. Defaults to `EventScheduled`. |
| `eventAttendanceMode` | EventAttendanceModeEnumeration | Required when not purely offline. See below. |
| `offers` | Offer | Ticket / fee info. `price` and `priceCurrency` must be set together. |
| `url` | URL | Canonical event page URL. |
| `inLanguage` | BCP-47 string | E.g. `"ja"` for Japanese events. |

## Three attendance modes

Set `eventAttendanceMode` to one of:

| Mode | IRI | Use for |
|---|---|---|
| Online | `https://schema.org/OnlineEventAttendanceMode` | Google Meet / Zoom 配信のみ |
| Offline | `https://schema.org/OfflineEventAttendanceMode` | 京都オフライン会場のみ |
| Mixed | `https://schema.org/MixedEventAttendanceMode` | ハイブリッド(会場+配信) |

### Location shape per mode

**Online** — single `VirtualLocation` with `url`:

```json
{
  "@type": "VirtualLocation",
  "url": "https://meet.google.com/abc-defg-hij"
}
```

**Offline** — single `Place` with `address` (PostalAddress):

```json
{
  "@type": "Place",
  "name": "京都リサーチパーク",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "下京区中堂寺南町134",
    "addressLocality": "京都市",
    "addressRegion": "京都府",
    "postalCode": "600-8813",
    "addressCountry": "JP"
  }
}
```

**Mixed** — array of both:

```json
[
  { "@type": "VirtualLocation", "url": "https://meet.google.com/..." },
  { "@type": "Place", "name": "...", "address": { ... } }
]
```

## `eventStatus` allowed values

| Value | Use when |
|---|---|
| `EventScheduled` | Default — event is on as planned |
| `EventCancelled` | Event will not happen |
| `EventPostponed` | New date TBA |
| `EventRescheduled` | New date set; also update `startDate` / `endDate` to the new times and provide `previousStartDate` |
| `EventMovedOnline` | Originally offline, now online — also update `eventAttendanceMode` to Online and `location` to VirtualLocation |

Stale `EventScheduled` on a past or cancelled event is the most common mistake.

## `offers` shape

```json
{
  "@type": "Offer",
  "price": "0",
  "priceCurrency": "JPY",
  "availability": "https://schema.org/InStock",
  "url": "https://miyakodeit.connpass.com/event/123456/",
  "validFrom": "2026-05-01T00:00:00+09:00"
}
```

- `price` and `priceCurrency` must be set together or both omitted
- Free events: `price: "0"` (string `"0"`, not number `0`)
- `availability`: `InStock` / `SoldOut` / `LimitedAvailability` / `PreOrder`

## Common mistakes

1. **Timezone offset missing on `startDate`** — `"2026-05-28T19:00:00"` is rejected; must be `"2026-05-28T19:00:00+09:00"`
2. **`url` on OfflineEvent location** — `url` is a `VirtualLocation` property only; on `Place` use `sameAs` or move it to the top-level Event `url`
3. **Hybrid event with single location** — `MixedEventAttendanceMode` requires both `VirtualLocation` and `Place`; using only one silently loses half the rich result
4. **`price` as number** — must be a string per Schema.org
5. **No `eventAttendanceMode`** — defaults vary by consumer; explicit IRI avoids ambiguity
6. **Past event stuck on `EventScheduled`** — update to `EventCancelled` / `EventRescheduled` or remove the JSON-LD entirely
7. **Image below 1200px wide** — rich results eligibility fails silently
8. **`endDate` before `startDate`** — Google drops the event from rich results
9. **`organizer` as plain string** — must be `Organization` or `Person` object with `@type`
10. **HTML in `name`** — `name` is plain text; markup is ignored or rejected

## Minimal valid examples

Online:

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "AI動画制作ハンズオン",
  "startDate": "2026-05-28T19:00:00+09:00",
  "endDate": "2026-05-28T21:00:00+09:00",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "VirtualLocation",
    "url": "https://meet.google.com/abc-defg-hij"
  },
  "organizer": {
    "@type": "Organization",
    "name": "みやこでIT",
    "url": "https://miyakodeit.com"
  }
}
```

Offline:

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "京都もくもく会",
  "startDate": "2026-06-15T13:00:00+09:00",
  "endDate": "2026-06-15T17:00:00+09:00",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "Place",
    "name": "京都リサーチパーク",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "下京区中堂寺南町134",
      "addressLocality": "京都市",
      "addressRegion": "京都府",
      "postalCode": "600-8813",
      "addressCountry": "JP"
    }
  }
}
```
