---
name: indexation-recovery
description: Diagnose why pages are missing from Google's index and fix the real cause. Starts from the GSC coverage drilldown CSV (the only source that reveals asset bloat, junk URLs, and legacy CMS paths — the Search Console API cannot see them), classifies every URL by required action, and separates cosmetic index bloat from actual lost search traffic. Use when the user says "インデックス", "未インデックス", "クロール済み未インデックス", "検出未インデックス", "indexed", "not indexed", "indexation", "coverage state", "GSC coverage", "インデックス登録されない", "検索に出ない", shows a Search Console screenshot, or asks why a page or site is not appearing in search. Also use proactively before telling anyone that an unindexed-page count will "decay on its own" — that claim is usually wrong and this skill explains how to check. Battle-tested on netsujo.jp (2026-07-21: caught a 9-day misdiagnosis) and miyakodeit.com.
---

# Indexation Recovery

Find out why pages are not in Google's index, and fix the cause that actually costs traffic.

The hard part is not fixing indexation. It is **not misdiagnosing it**. This skill is built around the failure mode that keeps recurring: confidently explaining a number you have never looked inside.

---

## The rule that matters most

**Get the GSC coverage drilldown CSV before forming any theory about the cause.**

This is not a nice-to-have first step. It is the difference between a correct diagnosis and a plausible fiction, because of a structural blind spot:

- The Index Coverage report has **no API that returns the URL list.**
- The Search Analytics API — the only API that *enumerates* URLs — returns only those with **impressions > 0**.
- The URL Inspection API can tell you about a URL, but only one you already know to ask about. It cannot hand you the population.
- Build assets (`/_next/static/*`, fonts, favicons) and junk URLs essentially never accumulate impressions.
- So they are **invisible to every API you have.** (Legacy CMS paths are a partial exception — if they still surface in results they do get impressions, which is exactly why an API-only view over-represents them.)

Investigate via API only and you will find the URLs the API can see — old CMS paths, a few thin pages — and attribute the whole number to them. The evidence will look solid. It will be wrong, and nothing in the API output will tell you so.

**Real incident (netsujo.jp, 2026-07-21).** "Crawled - not indexed: 1,437". An API-only investigation concluded the cause was legacy Wix URLs (`/iblog/`, `/nKkfwPVO/`), with sampled URL Inspection data backing it up. That diagnosis stood for 9 days and shaped the follow-up work. When the drilldown CSV was finally exported:

| Actual composition (1,000-row sample) | Count | Share |
|---|---|---|
| `/_next/static/chunks` (JS bundles) | 639 | 63.9% |
| `/_next/static/media` (fonts) | 288 | 28.8% |
| `/favicon.ico?…` | 70 | 7.0% |
| `opengraph-image` routes | 2 | 0.2% |
| **Real content pages** | **1** | **0.1%** |
| **Legacy Wix URLs** | **0** | **0.0%** |

994 of 1,000 carried `?dpl=<deployment-id>` — Vercel Skew Protection minting a fresh URL for every asset on every deploy. The true cause had already been found and written into `next.config.ts` two weeks earlier; the API-only investigation never read it.

Two lessons, both cheap to apply:
1. **Export the drilldown CSV first.** One request to the user, one minute of their time.
2. **Read existing code comments and prior docs before theorizing.** Someone may have already solved this.

### How to get the right CSV

Search Console → **ページのインデックス登録 / Page indexing** → **click the reason row** (e.g. 「クロール済み - インデックス未登録」) → **エクスポート / Export** on the page that opens.

The export from the top-level summary screen contains only a time series and per-reason counts — **no URLs**. It is easy to grab the wrong one; `scripts/classify-coverage-export.py` detects this and tells the user exactly where to click.

The drilldown export is **capped at 1,000 URLs**. If the report shows more, say so — the remainder is unobserved.

---

## Workflow

### 1. Classify the drilldown export

```bash
python3 scripts/classify-coverage-export.py <export.zip>          # zip goes in as-is
python3 scripts/classify-coverage-export.py <export.zip> --json   # machine-readable
python3 scripts/classify-coverage-export.py <export.zip> --list-real
```

Categories are cut by **what you would do about them**, not by URL shape:

| Category | What it means | Action |
|---|---|---|
| `build-asset` | `/_next/static/*` etc. | `X-Robots-Tag: noindex` on the asset path |
| `favicon-icon` | favicon / icon variants | Same — these usually fall outside the asset rule and get missed |
| `og-image-route` | `opengraph-image` routes | Same |
| `other-static-file` | stray `.woff2` / `.css` / images | Confirm origin, then noindex |
| `query-variant` | `?utm=`, `?page=` etc. | Usually fine if self-canonical — verify |
| `real-page` | **actual content** | The only category worth real effort |

The script also flags deploy-scoped cache busters (`?dpl=`, `?buildId=`, `?v=<hash>`) and counts distinct deployment IDs. Many distinct IDs means the number **grows with every deploy, and will not decay while the generator is still active**. Confirm whether it is still active by checking production HTML for the parameter — that is the difference between a frozen backlog and ongoing bleeding.

### 2. Fix asset bloat correctly

For assets, use `X-Robots-Tag: noindex` — **never `robots.txt` Disallow.**

Disallow blocks Googlebot from fetching the JS and CSS it needs to render your pages, which damages indexing of the real content. `noindex` keeps rendering intact and simply keeps the asset out of the index. Next.js example:

```ts
// next.config.ts — headers()
{ source: '/_next/static/:path*', headers: [{ key: 'X-Robots-Tag', value: 'noindex' }] },
// favicon and OG image routes are NOT covered by the rule above — they need their own entries
{ source: '/:file(favicon.ico|icon.png|apple-icon.png|icon.svg)', headers: [{ key: 'X-Robots-Tag', value: 'noindex' }] },
{ source: '/:path*/opengraph-image', headers: [{ key: 'X-Robots-Tag', value: 'noindex' }] },
```

Then stop the URL minting at the source if you can (disable Vercel Skew Protection, or pin the asset URL). `noindex` reclassifies the backlog into the "noindex" bucket over time; removing the parameter stops new ones appearing.

Expect the "excluded by noindex" count to **rise** as this works — that is the backlog migrating, not a regression. Say so before it happens, or it reads as damage.

### 3. Recover the real pages

Only `real-page` entries deserve per-URL work. Classify each by coverage state:

| Coverage state | Meaning | Recovery |
|---|---|---|
| Discovered - not indexed | Deprioritized before crawling | Internal links from indexed pages; make the page worth crawling |
| Crawled - not indexed | Crawled, judged thin or duplicate | Add original data; differentiate from near-duplicates |
| URL is unknown to Google | Never discovered | IndexNow + sitemap resubmit; verify a link exists from an indexed page |
| Alternate page with canonical | Canonical points elsewhere | Verify the HTML canonical is what you intend |
| Excluded by 'noindex' | Intentional | Confirm intent, then leave it |
| Blocked by robots.txt | Blocking | Check whether the block is still wanted |

**On the Indexing API — be honest with the client.** Google officially supports it only for `JobPosting` and `BroadcastEvent` pages. Using it for general pages is common practice and often appears to prompt a recrawl, but it is outside the documented contract and Google does not guarantee it. Do not present it as a supported fix. For general pages the sanctioned levers are sitemap submission, internal linking, and IndexNow (which covers Bing, not Google).

Before blaming content, confirm the technical basics — HTTP 200, self-canonical, `index,follow`, present in sitemap, linked from an indexed page. When all of those hold and Google still says "unknown", it is a **discovery** problem: submit via Indexing API and IndexNow, and check the page is not orphaned.

Do not claim a page is fine because these checks pass. They cover indexability, not quality, duplication, or link equity.

### 4. Redirects and legacy URL spaces

When a site migrated CMS (Wix, Studio, WordPress), Google keeps the old URL inventory for a long time — often discovered from the **old CMS's sitemaps**, which may now 404. You cannot delete that inventory from Google.

**Keep the redirects.** Converting `/oldpath/*` to robots.txt Disallow or 410 destroys the redirect signal and is actively counterproductive. Legacy URLs sitting in "Crawled - not indexed" are cosmetic; the redirect is doing its job.

Verify recrawl progress with URL Inspection `lastCrawlTime` rather than assuming decay. If those URLs are frozen months in the past, they are not being reprocessed — but check first whether they are even a meaningful share of the total (step 1). At netsujo.jp they were 0%.

---

## Report the right number

**Never use the raw unindexed count as a KPI.** It is dominated by assets and legacy noise, and it moves for reasons unrelated to business outcomes. Report these instead:

1. **Indexed rate of sitemap URLs.** Sample with URL Inspection (fixed seed) and give a confidence interval. netsujo.jp: 88.2% (30/34 sampled → est. 169/192).
2. **Search exposure actually lost.** Sum impressions of URLs that are unindexed *and* had impressions > 0, as a share of site total. netsujo.jp: 548 / 86,465 = **0.63%** — against a headline number of 1,437.

When several real pages need work, order them by impressions, then by whether they sit on a conversion path. A page with 140 impressions and a CTA outranks five pages with zero.

Call this "lost search exposure", not "lost revenue" — impressions are not conversions, and treating them as such overstates the case.

Also read the coverage time series (the summary CSV is genuinely useful here): unindexed counts move in **steps** on GSC's batch-refresh days, not smoothly. Per-day averages computed across a step are meaningless. Check whether *indexed* is rising at the same time — at netsujo.jp it went 127 → 196 (+54%) while the scary number also grew.

---

## Claims to avoid

The statements most likely to be wrong, in rough order of how often they get made:

- **"It will decay on its own."** Only true if new URLs have stopped being created. Verify with the latest `lastCrawlTime` among affected URLs, and by confirming the generator (e.g. `?dpl=`) is gone from production HTML.
- **"The cause is X"** based only on API data. The API cannot see most of these URLs. Say "in the observed sample" and give the sample size.
- **"N pages are missing from search."** Most are assets. Report the `real-page` count separately.
- Extrapolating a recrawl rate from impression-bearing URLs. Those are Google's higher-value URLs; the rest move slower.

State the sampling limit (1,000 of N) every time. It is the difference between a finding and an overclaim.

---

## Deliverable structure

```markdown
## 結論
[cause, with sample size and confidence]

## 実際の内訳
[classifier table — category / count / share]

## 本当の実害
- サイトマップ掲載ページの indexed 率: X%（サンプル n、CI）
- 未インデックスで失っている検索露出: X impressions（サイト全体の Y%）
- 対応が必要な実コンテンツページ: N件

## 対応
[executed vs. proposed, clearly separated]

## 未確定・限界
[sampling cap, unverified causal claims, what would resolve them]
```

Keep "executed" and "proposed" visibly separate — conflating them is how a report becomes a promise no one made.

---

## Related skills

- `gsc-weekly-audit` — routine monitoring; run this first to notice drift early
- `bing-indexnow` — IndexNow submission (reaches Bing/Copilot; Google does not consume IndexNow)
- `link-integrity-tester` — orphan and broken-link detection when a page is undiscovered

## Reference

Cite these in client deliverables — the recommendations above are not opinions, and saying so is what makes the report defensible.

- Coverage report: https://developers.google.com/search/docs/monitor-debug/search-console-coverage
- `noindex` requires the page to be crawlable (i.e. not blocked in robots.txt), which is why Disallow is the wrong tool: https://developers.google.com/search/docs/crawling-indexing/block-indexing
- robots.txt is for controlling crawl volume, not for keeping pages out of the index: https://developers.google.com/search/docs/crawling-indexing/robots/intro
- **Indexing API is documented for `JobPosting` and `BroadcastEvent` only**: https://developers.google.com/search/apis/indexing-api/v3/quickstart (quota: https://developers.google.com/search/apis/indexing-api/v3/quota-pricing)
- Permanent redirects are the supported way to move URLs: https://developers.google.com/search/docs/crawling-indexing/301-redirects
- IndexNow (Bing/Yandex/Seznam/Naver — not Google): https://www.indexnow.org/documentation
- Full case study: `netsujo-web/docs/seo/2026-07-21-indexation-followup.md`
