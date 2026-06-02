---
name: bing-indexnow
description: Submit URLs to IndexNow (Bing/Yandex/Seznam/Naver) for instant indexation. Critical for AI search because 87% of ChatGPT Search citations and 100% of Microsoft Copilot citations come from the Bing index. Use when user says "IndexNow", "Bing indexation", "Copilot SEO", "ChatGPT Search SEO", "AI search indexation", "new article publish", "URL submit", "instant index" or after publishing/updating any blog article. Battle-tested on miyakodeit.com (51 sessions/90d via Bing).
---

# Bing IndexNow Submitter

Submits URLs to the IndexNow protocol so Bing, Yandex, Seznam, and Naver index them within minutes (instead of weeks). Auto-discovers the IndexNow key file location, falls back to manual key, and supports both single-URL ping and bulk submission.

## Why this matters in 2026

Per the 2026-06-02 analytics review:

- **ChatGPT Search** sources 87% of its citations from Bing's top 10 results (not Google's). Optimizing for Bing = optimizing for ChatGPT
- **Microsoft Copilot** is 100% backed by the Bing index
- **Perplexity** uses real-time search and respects IndexNow signals
- IndexNow is the only push-based indexation protocol; Google Indexing API only accepts job postings and live streams, not editorial content (Google ignored editorial submissions since 2023)

Netsujo monorepo current state:
- netsujo.jp: Bing 21 sessions/28d (33% of Google's volume)
- miyakodeit.com: Bing 40 sessions/90d (17% of Google's volume) + ChatGPT 8 referrals
- Both sites have no IndexNow configured → AI search opportunity left on the table

## What this skill does

1. **Discover the IndexNow key**
   - Look for `public/{key}.txt` in the repo root or scan for files matching `^[a-f0-9]{32}\.txt$`
   - If not found, generate a new 32-character hex key, place the file in `public/`, and inform the user to commit it
2. **Validate the key file is publicly accessible**
   - `curl https://{domain}/{key}.txt` must return 200 with the key as body
3. **Submit URLs**
   - Single URL: `POST https://api.indexnow.org/IndexNow?url={url}&key={key}` (one request, all engines)
   - Bulk (up to 10000 URLs): `POST https://api.indexnow.org/IndexNow` with JSON body `{host, key, keyLocation, urlList}`
4. **Verify**
   - Bing Webmaster Tools API to confirm receipt (if credentials available)
5. **Report**
   - URL list, status codes, timing, retry advice

## Critical rules (enforced)

- The key file MUST be at `https://{domain}/{key}.txt` — placing it elsewhere fails silently
- Both `www` and non-`www` hostnames need separate keys if served as separate properties
- Don't submit URLs that return 404/5xx — IndexNow blacklists abusing keys
- Don't submit URLs that have `noindex` — IndexNow accepts but Bing rejects later
- Maximum 10,000 URLs per bulk call

## Usage patterns

### Pattern 1: After publishing a new blog post

```
> 新しいブログ記事 https://netsujo.jp/blog/news-x 公開した。IndexNow送信
```

The skill submits the single URL, verifies key accessibility, and reports status.

### Pattern 2: Bulk submission of high-priority pages

```
> Bing最適化したい主要20URLをIndexNowにバルク送信して
```

The skill collects URLs from sitemap.xml top entries by `<lastmod>`, batches them in one call, and reports.

### Pattern 3: First-time setup (no key yet)

```
> miyakodeitにIndexNow導入して
```

The skill generates a key, creates `public/{key}.txt`, instructs to commit + deploy, then verifies the key is publicly accessible before submitting.

## Integration points

- **netsujo monorepo conventions**: respect `feedback_no_japanese_ascii_space.md`, generate commit messages in Japanese without half-width spaces between JP and ASCII
- **CI integration**: Provides a GitHub Actions workflow snippet that auto-pings IndexNow when `public/sitemap.xml` changes on `main`
- **GA4 cross-check**: Pulls `source/medium = bing / organic` for the last 28 days to measure IndexNow impact (compare 28 days before/after)

## Output

Each submission produces:

```
{
  "submitted": 6,
  "success": 6,
  "failed": 0,
  "engines_notified": ["api.indexnow.org (Bing/Yandex/Seznam/Naver)"],
  "urls": [...],
  "key_location": "https://netsujo.jp/abc123....txt",
  "next_steps": [
    "Bing Webmaster Tools で受信確認(通常24時間以内)",
    "GA4 で source=bing/organic の推移を 28 日後に確認"
  ]
}
```

## References

- IndexNow official protocol: https://www.indexnow.org/documentation
- Bing Webmaster IndexNow guide: https://www.bing.com/webmasters/url-submission-api
- ChatGPT Search Bing dependency: https://www.leapd.ai/blog/ai-visibility/how-chatgpt-google-ai-overviews-and-perplexity-source-information-in-2026
- Microsoft Copilot Bing source: confirmed via Microsoft Search Blog (2025)
