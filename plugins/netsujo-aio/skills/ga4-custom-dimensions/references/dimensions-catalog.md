# GA4 Custom Dimensions Catalog

Full specification of the 12 standard custom dimensions registered by `ga4-custom-dimensions.py`. Use this as the source of truth when wiring GTM dataLayer pushes, building Looker Studio reports, or debugging missing data in GA4 Explorations.

## Scope primer

GA4 has three dimension scopes, and **scope is immutable after registration**. Choose carefully.

| Scope | Lives on | Use when | Hard cap |
|---|---|---|---|
| `EVENT` | Single event hit | Value changes per interaction (button click, page view) | 50 per property |
| `USER` | All future events for that user | Value describes the user (tier, language) and is sticky | 25 per property |
| `ITEM` | Item array inside ecommerce events | E-commerce product attributes | 10 per property |

Rule of thumb: if the value can change while the user stays on the site, it is event-scoped. If it changes only on signup/login, it is user-scoped.

## The 12 dimensions

### 1. `cta_label` (event-scoped)

- **Display name**: CTAラベル
- **Description**: CTA button label clicked by user
- **GTM dataLayer**:
  ```js
  dataLayer.push({
    event: 'cta_click',
    cta_label: '無料で相談する',
    cta_position: 'hero',
  });
  ```
- **Use cases**: A/B test CTA copy, identify highest-converting wording per page
- **Battle-tested**: miyakodeit.com 2026-05-27 manual registration の自動化対象

### 2. `cta_position` (event-scoped)

- **Display name**: CTA位置
- **Description**: Location of CTA on the page (hero/footer/sidebar)
- **Allowed values**: `hero` / `footer` / `sidebar` / `inline` / `sticky`
- **Pairs with**: `cta_label` (always send together)
- **Looker Studio tip**: pivot rows = `cta_position`, cols = `cta_label`, metric = conversion rate

### 3. `article_category` (event-scoped)

- **Display name**: 記事カテゴリ
- **Description**: Blog article category slug
- **Source**: Strapi `article.category.slug`
- **Fires on**: `page_view`, `scroll`, `read_completion`
- **Battle-tested**: 2026-05-28 AI動画イベントレポート以降、カテゴリ別離脱率分析で使用中

### 4. `article_author` (event-scoped)

- **Display name**: 記事著者
- **Description**: Author name of the article
- **Source**: Strapi `article.author.name`
- **Why event-scoped, not user-scoped**: One reader reads multiple authors. The author is a property of the content, not the reader.

### 5. `event_attendance_mode` (event-scoped)

- **Display name**: イベント参加形態
- **Allowed values**: `Online` / `Offline` / `Mixed`
- **Source**: Strapi `event.attendanceMode` (matches schema.org `EventAttendanceModeEnumeration`)
- **Fires on**: `event_register`, `event_view`
- **Pairs with**: structured data `Event` schema

### 6. `outbound_domain` (event-scoped)

- **Display name**: 外部リンク先ドメイン
- **Description**: Domain of clicked outbound link
- **GTM trigger**: built-in "Click - Just Links" with regex `^https?://(?!.*miyakodeit\.com|.*netsujo\.jp)`
- **Use case**: identify which external resources drive engagement (e.g. connpass, GitHub)

### 7. `search_query` (event-scoped)

- **Display name**: サイト内検索クエリ
- **Description**: User-entered site search query
- **Note**: GA4 has a built-in `search_term` parameter but it is not exposed as a dimension by default. Register a custom dimension that reads the same parameter.
- **Privacy**: lowercase + trim before pushing; never log PII

### 8. `user_tier` (user-scoped)

- **Display name**: ユーザー階層
- **Allowed values**: `free` / `paid` / `enterprise` / `internal`
- **Set via**: `gtag('set', 'user_properties', { user_tier: 'paid' })` on login
- **Why user-scoped**: tier persists across sessions until upgrade/downgrade

### 9. `signup_source` (user-scoped)

- **Display name**: サインアップ流入元
- **Description**: Channel that drove the signup (utm_source at signup time, frozen)
- **Set via**: `user_properties` once at signup; never overwrite later
- **Why user-scoped**: the originating channel is a permanent attribute of the user

### 10. `read_completion_pct` (event-scoped)

- **Display name**: 読了率
- **Allowed values**: `25` / `50` / `75` / `100`
- **GTM trigger**: built-in scroll depth trigger at 25/50/75/90%, mapped to 25/50/75/100
- **Battle-tested**: 2026-05-28 以降、`article_category` × `read_completion_pct` ダッシュボードで「どのカテゴリが読み切られているか」を分析

### 11. `language_pref` (user-scoped)

- **Display name**: 言語設定
- **Allowed values**: BCP-47 codes (`ja`, `en`, `ja-JP`)
- **Source**: `navigator.language` or user preference cookie
- **Why user-scoped**: language choice is sticky for the user across sessions

### 12. `experiment_variant` (event-scoped)

- **Display name**: A/Bテスト variant
- **Description**: Variant assigned in an A/B experiment
- **Format**: `<experiment_id>:<variant>` e.g. `hero_copy_v3:control`
- **Why event-scoped**: same user may participate in multiple experiments across sessions
- **Pairs with**: Google Optimize successor (GrowthBook, Statsig) integration via dataLayer

## GA4 Admin API rate limits

Per [official docs](https://developers.google.com/analytics/devguides/config/admin/v1/quotas):

| Limit | Value |
|---|---|
| Tokens per project per day | 50,000 |
| Tokens per project per hour | 5,000 |
| Tokens per property per hour | 500 |
| Concurrent requests per project | 10 |

A `customDimensions.create` call costs 1 write token. Registering all 12 dimensions costs ~12 read tokens (list) + 12 write tokens. Well below limits.

The skill retries with exponential backoff on `429` / `503`.

## How to pick scope (decision tree)

```
Does the value describe the user across sessions?
├─ Yes → user-scoped
│         (user_tier, signup_source, language_pref)
│
└─ No → event-scoped
         ├─ Is it a property of an e-commerce item?
         │  └─ Yes → item-scoped (none in standard 12)
         └─ No → event-scoped (everything else)
```

If unsure, default to **event-scoped**. Event-scoped has the largest cap (50) and can always be aggregated by `userId` later if needed.

## Common mistakes

1. **Registering the same parameter under two scopes**: GA4 rejects this at the parameterName uniqueness check. The skill catches this via `(parameterName, scope)` dedupe and aborts with exit code 2.
2. **Trying to change scope after registration**: not possible via API. You must delete and recreate, which **loses all historical data** under that dimension. The skill prints a `[conflict]` warning instead of silently doing this.
3. **Display name collision**: two dimensions cannot share a display name across all scopes. Prefix with scope tag if needed (`[U] 言語設定` for user-scoped).
4. **Firing events before registration**: events fired before the dimension exists are accepted but the dimension column stays empty for those rows. Always register first, then fire.
5. **Forgetting to mark as conversion**: custom dimensions are not conversion events. If you want `cta_click` to count as a conversion, mark the **event** as conversion in the GA4 Events UI (or via `ga4-conversion-events` skill).
6. **PII in custom dimensions**: GA4 ToS prohibits PII in dimensions. Hash or omit email, phone, full name before pushing.

## Looker Studio quick wins

Once dimensions are populated, these reports become trivial:

| Report | Dimensions | Metric |
|---|---|---|
| Best CTA per page | `page_path`, `cta_label`, `cta_position` | conversion rate |
| Article funnel by category | `article_category`, `read_completion_pct` | event count |
| Online vs offline event RSVPs | `event_attendance_mode` | `event_register` count |
| Signup channel LTV | `signup_source`, `user_tier` | revenue |
| Experiment lift | `experiment_variant` | conversion rate |

## Verification after apply

```bash
# 1. confirm registration
python3 ga4-custom-dimensions.py --property 531238165 --list

# 2. fire a test event from the site
# (browser console)
dataLayer.push({event:'cta_click', cta_label:'test', cta_position:'hero'})

# 3. check GA4 DebugView (Admin → DebugView) within 60 seconds
# Custom dimension columns should appear with the values you pushed
```

If DebugView shows the event but the custom dimension column is empty, the most common cause is a typo in `parameterName` between the GTM tag and the registered dimension (case-sensitive).
