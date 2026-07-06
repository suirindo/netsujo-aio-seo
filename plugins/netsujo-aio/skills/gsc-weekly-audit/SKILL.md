---
name: gsc-weekly-audit
description: Run a comprehensive Google Search Console audit covering Sitemap status, URL Inspection, Search Analytics, canonical mismatch detection, CTR diagnosis, and 0-impression page detection. Battle-tested on miyakodeit.com and netsujo.jp with weekly GitHub Actions cron. Use when user says "GSC audit", "Search Console weekly check", "indexing audit", "canonical mismatch", "CTR low pages", or wants automated site health monitoring.
---

# GSC Weekly Full Audit

Production-tested Google Search Console audit pipeline. Runs 8 sequential checks and produces a Critical / Warning / Info report with actionable recommendations. Designed to catch issues that single-API checks miss (e.g., sitemap success but URL-level Discovered-not-indexed).

## What it checks

1. **Sitemap status**: All registered sitemaps via Sitemaps API. Detects errors, warnings, and unread sitemaps.
2. **URL Inspection**: Top 30 URLs (config) for `verdict` / `coverageState` / `indexingState` / `lastCrawlTime`. Catches `Discovered - currently not indexed`, `URL is unknown to Google`, `Blocked due to access forbidden`.
3. **Search Analytics**: Query/page/country/device breakdown over 7-day window. Top 50 queries + page impressions + CTR + position.
4. **Canonical mismatch**: User-declared canonical vs Google-selected canonical. Critical for /blog, /events, dynamic routes.
5. **CTR low pages**: Pages with impressions > 100 and CTR < 1.0% in last 28 days. Suggests title/description rewrite candidates.
6. **0-impression pages**: Indexed pages with 0 impressions in 28 days. Possible thin content or wrong intent.
7. **Discovered count**: Pages submitted to sitemap but still "Discovered, not indexed".
8. **Sitemap lastmod drift**: Real lastmod (file mtime) vs declared lastmod. Google distrusts wrong lastmod.

## When to use

Use this skill when:
- User asks for "GSC audit", "Search Console check", "site indexing health"
- Setting up weekly automated monitoring for a Next.js / Strapi / static site
- Diagnosing why specific URLs are not indexed
- Identifying CTR optimization candidates
- Investigating canonical issues after site migration

## Prerequisites

1. **Google Cloud project** with Search Console API enabled
2. **Service account JSON** at `~/.config/gcloud/gsc-credentials.json` (default) or path via `GSC_CREDENTIALS_PATH` env var
3. **GSC property access** for the service account (Owner or Full user)
4. Python 3.10+ with `google-api-python-client`, `google-auth`, `requests`

```bash
pip install google-api-python-client google-auth requests
```

## Usage

### Basic audit (single property)

```bash
python3 scripts/gsc-weekly-audit.py \
  --site "sc-domain:example.com" \
  --days 7
```

### With Discord notification

```bash
python3 scripts/gsc-weekly-audit.py \
  --site "sc-domain:example.com" \
  --discord
```

Set `DISCORD_WEBHOOK` env var (NOT `DISCORD_WEBHOOK_URL` — the scripts read `os.environ.get("DISCORD_WEBHOOK")`). Critical findings trigger red embed, warnings orange, info blue.

### GitHub Actions weekly cron

Workflow「GSC 週次フル監査」 runs every Monday 09:00 JST in both miyakodeit and netsujo-web repos and posts to Discord. Webhook is stored as repo secret `DISCORD_WEBHOOK` (`gh secret set DISCORD_WEBHOOK`).

### Output

- **Console**: Categorized table (Critical / Warning / Info)
- **JSON report**: `reports/gsc/audit-YYYY-MM-DD.json`
- **CSV exports**: `reports/gsc/url-inspection.csv`, `reports/gsc/ctr-low.csv`
- **Markdown summary**: `reports/gsc/audit-YYYY-MM-DD.md` for PR-style review

## Configuration

Override defaults via env vars or CLI flags:

| Setting | Default | Override |
|---|---|---|
| Inspection URL count | 30 | `--inspect-count 50` |
| Search Analytics window | 7 days | `--days 28` |
| CTR low threshold | 1.0% | `--ctr-threshold 0.5` |
| Min impressions for CTR check | 100 | `--min-impressions 50` |
| Top URLs source | sitemap top-30 | `--urls-file urls.txt` |

## Reference implementations

実運用中のスクリプト本体（このスキルディレクトリには同梱していない）:

- `miyakodeit/scripts/gsc-weekly-audit.py` — miyakodeit.com 用（sc-domain:miyakodeit.com）
- `netsujo-web/scripts/gsc-weekly-audit.py` — netsujo.jp 用（URL-prefix `https://netsujo.jp/` + GA4 property 382871067）
- 各リポの GitHub Actions workflow「GSC 週次フル監査」— cron テンプレート

## Battle-tested patterns

This skill encodes lessons learned from 6 months of weekly audits on `miyakodeit.com` (564 community members) and `netsujo.jp` (Web3/AI consultancy):

- **2026-05-10 incident**: Fake sitemap `/blog/meetup-anxiety` shipped to Google. Caught 7 days late because we didn't run `sitemaps.list()` weekly. Now mandatory.
- **2026-05-11 incident**: `/blog` page had duplicate title from layout template. Caught 5 days late. Now we cross-check sitemap title vs rendered HTML title.
- **2026-05-17 rule**: "GSC weekly full audit is mandatory before ANY content shipping. No exceptions." (CLAUDE.md)

These rules are encoded as default-on Critical-level alerts in this audit.

## Related skills

- `netsujo-aio:indexation-recovery` — Discovered/Crawled-not-indexed の診断と復旧
- `netsujo-aio:bing-indexnow` — Bing/IndexNow への即時インデックス送信
- `netsujo-aio:jsonld-faqpage` — Fix rich result eligibility
- `claude-seo:seo-technical` — Broader technical SEO audit (complements this)
