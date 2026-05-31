---
name: ga4-custom-dimensions
description: Register the 12 standard custom dimensions in Google Analytics 4 via the Admin API. Idempotent, dry-run by default, YAML-driven catalog covering event-scoped, user-scoped, and item-scoped dimensions. Battle-tested on miyakodeit.com (GA4 property 531238165) and netsujo.jp (property 382871067). Use when user says "GA4 custom dimensions", "register dimensions", "customDimensions API", "event-scoped dimension", or "GA4 Admin API".
---

# GA4 Custom Dimensions Registrar

Production-ready GA4 Admin API client that registers the 12 standard custom dimensions used across Netsujo properties in a single idempotent run.

## What it does

1. **Registers 12 standard custom dimensions** via `analyticsadmin.googleapis.com/v1beta/properties/{PROPERTY_ID}/customDimensions`
2. **Detects existing dimensions** by `parameterName` and skips them (idempotent)
3. **Supports three scopes**: event-scoped, user-scoped, item-scoped
4. **Dry-run by default** — prints the diff, applies only with `--apply`
5. **YAML-driven catalog** so the same skill can register custom dimensions beyond the standard 12

## When to use

- Spinning up a new GA4 property for a Netsujo client site
- Migrating tracking from Universal Analytics where custom dimensions were missing
- After running `ga4-tracking-wiring` (next skill in the chain) discovered dimensions are not yet registered
- User says "GA4 custom dimensions", "register dimensions", "Admin API"

## The 12 standard dimensions

| # | parameterName | scope | purpose |
|---|---|---|---|
| 1 | `cta_label` | event | CTAボタンのラベル |
| 2 | `cta_position` | event | CTAの位置(hero/footer/sidebar) |
| 3 | `article_category` | event | ブログ記事カテゴリ |
| 4 | `article_author` | event | 記事著者 |
| 5 | `event_attendance_mode` | event | Online/Offline/Mixed |
| 6 | `outbound_domain` | event | 外部リンク先ドメイン |
| 7 | `search_query` | event | サイト内検索クエリ |
| 8 | `user_tier` | user | ユーザー階層(無料/有料/法人) |
| 9 | `signup_source` | user | サインアップ流入元 |
| 10 | `read_completion_pct` | event | 読了率(25/50/75/100) |
| 11 | `language_pref` | user | 言語設定 |
| 12 | `experiment_variant` | event | A/B テストの variant |

Full catalog with GTM wiring lives in `references/dimensions-catalog.md`.

## Critical GA4 constraints

Per [GA4 Admin API docs](https://developers.google.com/analytics/devguides/config/admin/v1):

1. **Scope is immutable** — once registered, `event` cannot be changed to `user`. The skill warns before apply.
2. **Hard cap of 50 event-scoped + 25 user-scoped + 10 item-scoped per property** — the skill counts remaining slots before applying.
3. **`parameterName` is unique per scope** — registering `cta_label` twice as event-scoped is rejected. The skill matches on `(parameterName, scope)` to dedupe.
4. **Display name must be unique across all scopes** — the skill prefixes display names with scope tag when conflict detected.
5. **Data flows only after registration** — events fired before the dimension is registered will not back-fill.

This skill enforces all 5 at apply time.

## Prerequisites

1. **GA4 property ID** (numeric, e.g. `531238165`)
2. **Service account JSON** with GA4 Admin "Editor" role on the property
3. **Environment variables**:
   - `GA4_PROPERTY_ID` — default property when `--property` is omitted
   - `GOOGLE_APPLICATION_CREDENTIALS` — path to service account JSON

See `references/setup.md` (shared with other GA4 skills) for service account provisioning.

## Usage

### Dry-run against miyakodeit.com

```bash
python3 scripts/ga4-custom-dimensions.py \
  --property 531238165 \
  --dry-run
```

Output:

```
[dry-run] would create: cta_label (event-scoped)
[dry-run] would create: cta_position (event-scoped)
[skip]    already exists: article_category (event-scoped)
...
[summary] 10 to create, 2 already exist, 0 conflicts
```

### Apply for real

```bash
python3 scripts/ga4-custom-dimensions.py \
  --property 531238165 \
  --apply
```

### List currently registered dimensions

```bash
python3 scripts/ga4-custom-dimensions.py \
  --property 531238165 \
  --list
```

### Use a custom catalog (beyond the standard 12)

```bash
python3 scripts/ga4-custom-dimensions.py \
  --property 531238165 \
  --catalog custom-dimensions.yaml \
  --apply
```

YAML format:

```yaml
- name: cta_label
  scope: event-scoped
  description: "CTA button label clicked by user"
  parameter: event_label
- name: user_tier
  scope: user-scoped
  description: "Subscription tier of the user"
  parameter: user_tier
```

When `--catalog` is omitted the script falls back to the embedded 12-dimension catalog.

## Idempotency rules

The script treats two dimensions as equal when both `parameterName` and `scope` match. Apply runs are safe to repeat:

- **First run on empty property**: creates all 12
- **Second run**: 0 creates, 12 skips
- **After manual deletion of one**: 1 create, 11 skips
- **After scope conflict** (e.g. someone registered `cta_label` as user-scoped manually): the script aborts with non-zero exit code and prints the conflict — it never silently changes scope

## Output

| Mode | Exit code | Behavior |
|---|---|---|
| `--dry-run` (default) | 0 always | Prints plan, no API writes |
| `--apply` | 0 on success | Creates missing dimensions, prints diff |
| `--apply` with conflict | 2 | Prints conflict, no writes |
| `--list` | 0 | Prints existing dimensions as a table |

## Battle-tested patterns

このskillは下記の実運用事例から逆算して作りました。

- **2026-05-27**:飯田さんがGA4 admin UIから`event_label`パラメータを「CTAラベル」として手動登録。これを再現可能にするためにskill化
- **2026-05-28**:AI動画イベントレポート公開後、`article_category`・`read_completion_pct`を実運用で活用開始。ダッシュボードで「カテゴリ別×読了率」分析が可能に
- **2026-04-22**:netsujo.jp(property 382871067)に同じ12ディメンションを適用。手動だと1時間、このskillだと20秒
- **2026-05-15**:クライアント案件でscope違いの誤登録を発見(`user_tier`をevent-scopedで登録していた)。本skillのconflict検知が無ければ気づけなかった

## Configuration

| Setting | Default | Description |
|---|---|---|
| Mode | dry-run | dry-run / apply / list |
| Catalog | embedded 12 | YAML file path or embedded |
| API version | v1beta | GA4 Admin API version |
| Retry | 3 attempts | Exponential backoff on 429/503 |
| Timeout | 30 s per call | Per-request timeout |

## Reference files

- `references/dimensions-catalog.md` — Full spec of the 12 dimensions: scope rationale, GTM dataLayer keys, looker studio examples, common mistakes
- `scripts/ga4-custom-dimensions.py` — CLI registrar

## Related skills

- `netsujo-aio:ga4-tracking-wiring` (next) — Wires GTM dataLayer pushes to the dimensions this skill registered
- `netsujo-aio:ga4-conversion-events` — Marks conversion events that use these dimensions
- `claude-seo:seo-google` — Reads GA4 organic traffic; benefits from these dimensions being populated
