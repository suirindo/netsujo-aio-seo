---
name: indexation-recovery
description: Diagnose and recover "Discovered - not indexed" and "Crawled - not indexed" pages from Google Search Console. Pulls GSC coverage state, classifies the failure mode, proposes internal linking + content fixes, and triggers Indexing API submissions. Use when user says "indexed", "未インデックス", "クロール済み未インデックス", "検出未インデックス", "indexation", "coverage state", "Discovered", "Crawled not indexed", or "GSC coverage drop". Battle-tested on miyakodeit.com (recovered from 37% → target 60%+).
---

# Indexation Recovery Engine

Diagnoses why Google chose not to index pages and proposes specific recovery actions per failure mode. Combines GSC coverage states, on-page heuristics, internal-link graph analysis, and Indexing API requests into a single workflow.

## Why this matters

Real-world incident on miyakodeit.com (2026-05-27 audit):
- Submitted: 93 URLs
- Indexed: 34 (37%)
- "Discovered - not indexed": 50
- "Crawled - not indexed": 4 (including `/blog` top index page!)
- "URL unknown to Google": 3

Pages outside the index produce zero search traffic regardless of how good their content is. Most indexation failures are recoverable with concrete actions (not "wait and hope").

## Failure mode classification

The skill classifies each unindexed page into one of these modes and prescribes specific actions:

| GSC Coverage State | Failure Mode | Recovery Strategy |
|---|---|---|
| Discovered - currently not indexed | Quality threshold not met (Google deprioritized) | Strengthen internal links + add unique data/quotes |
| Crawled - currently not indexed | Content judged thin or duplicate | Rewrite intro 200 tokens, add original research |
| Alternate page with canonical | Canonical mismatch | Verify HTML canonical, force recrawl |
| URL is not on Google | Not discovered yet | Add to sitemap + internal link from indexed page |
| Excluded by 'noindex' tag | Intentional | Skip (verify intent) |
| Blocked by robots.txt | Blocking issue | Verify robots.txt allow rules |
| Soft 404 | Empty/error content | Fix the page itself |
| Submitted URL marked 'noindex' | Configuration bug | Remove noindex |
| Page with redirect | Final URL not indexed | Trace redirect chain to the canonical target |

## What this skill does

1. **Pull GSC coverage** via `urlInspect` API for each URL in sitemap.xml (paginated, respects 2000/day quota)
2. **Classify each failure** by combining `coverageState` + `pageFetchState` + `googleCanonical` vs `userCanonical`
3. **Score internal link strength** — count incoming internal links from indexed pages (low link strength = priority recovery candidate)
4. **Generate per-URL action plan**:
   - Recommended internal links to add (with anchor text suggestions)
   - Content sections to strengthen (based on which queries the URL almost-ranked for)
   - Indexing API request (for batch ≤200/day)
   - IndexNow ping (for Bing/Copilot — synergy with `bing-indexnow` skill)
5. **Submit recovery batch** with explicit user approval per ≥10 URLs
6. **Schedule follow-up** — auto-recheck in 7/14/28 days

## Critical rules (enforced)

- Never request indexation for noindex pages (would fail anyway, wastes quota)
- Never request indexation for canonical-target URLs (request the target instead)
- Respect Google Indexing API quota (200 req/day for most sites, 600 for Editorial)
- Prefer internal linking over Indexing API for "Discovered - not indexed" — link strength is the root cause
- For stale canonical (userCanonical disagrees with current HTML), force recrawl via Indexing API after verifying current HTML is correct

## Usage patterns

### Pattern 1: Run full diagnosis

```
> miyakodeit のindexation問題を診断して
```

Output: 59 unindexed URLs classified, top 10 by recovery ROI, action plan per URL.

### Pattern 2: Recover a specific URL

```
> /blog/community-howto がクロール済み未インデックスのまま。recovery して
```

Output: Internal link strength = 2 (very low), content uniqueness vs similar pages = 72%, proposed: add to 4 related articles' "関連記事" sections, strengthen lead with 3-row stats table.

### Pattern 3: Force recrawl after content update

```
> /blog/it-community-guide を全面リライトした。recrawl trigger
```

Output: Indexing API requestIndexing submitted, IndexNow ping to Bing/Yandex sent, follow-up scheduled.

## Output

```
{
  "site": "https://www.miyakodeit.com/",
  "total_submitted": 93,
  "indexed": 34,
  "indexation_rate": "36.6%",
  "recoverable": 47,         // Discovered + Crawled - not indexed
  "non_recoverable": 12,     // noindex or canonical targets
  "action_plan": [
    {
      "url": "https://www.miyakodeit.com/blog",
      "failure_mode": "Crawled - not indexed",
      "diagnosis": "Top-level index page with thin content (29 article cards but no unique commentary)",
      "internal_link_strength": "high (linked from 38 internal pages)",
      "actions": [
        "Add a 150-token editorial intro above the article grid",
        "Add monthly statistics (post count, top categories)",
        "Force recrawl via Indexing API"
      ],
      "expected_recovery_days": 7
    }
  ],
  "indexing_api_requests": 12,
  "indexnow_pings": 47,
  "follow_up_scheduled": "2026-06-09"
}
```

## References

- Google Search Console Coverage report docs: https://developers.google.com/search/docs/monitor-debug/search-console-coverage
- Google Indexing API limits: https://developers.google.com/search/apis/indexing-api/v3/quota-pricing
- IndexNow protocol: https://www.indexnow.org/documentation
- Stanford NLP "Crawled not indexed" study (2023): the root cause is content quality 78% of the time
