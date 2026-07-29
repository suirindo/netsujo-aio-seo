---
name: ai-citation-tracker
description: Track brand and domain citations in ChatGPT/Perplexity/Gemini/AI Overviews over time. Issues structured queries, captures citation lists from each engine's response, persists snapshots, and reports week-over-week changes in citation share. Use when user says "AI citation", "AI流入", "ChatGPT引用", "Perplexity citation", "AI Overview mention", "brand visibility in AI", "GEO tracking", "share of AI voice", or "LLM SEO monitoring". Use proactively after content publication to measure GEO uplift.
---

# AI Citation Tracker

Defines a fixed query set per topic cluster, sends each query to ChatGPT/Perplexity/Gemini (and approximates AI Overview via SerpAPI), captures the citation links, and stores daily/weekly snapshots so brand visibility in AI search can be measured longitudinally — not just inferred from referral traffic.

## Why this matters in 2026

Referral traffic from AI engines (`chatgpt.com`, `perplexity.ai`, `copilot.com`) is a lagging indicator — by the time it shows up in GA4, the citation was made days ago. This skill is a leading indicator:

- GA4 AI-referral sessions and observed AI citations answer different questions and must be reported separately
- A citation snapshot measures only its declared engine/model/locale/variant conditions
- Do not forecast downstream traffic from mentions unless an explicit, source-backed model is supplied
- Without tracking we cannot tell whether content changes (Phase 1 retitles, intro rewrites) actually improve AI citation share

## What this skill tracks

For each topic cluster (defined in `config/clusters.yml`):

1. **Query set** — 10-30 representative search queries that real users would issue (e.g., "Web3 京都 開発会社", "DID とは", "もくもく会 京都")
2. **Engine matrix** — ChatGPT (via Playwright), Perplexity (API), Gemini (via Google AI Studio), AI Overview (via SerpAPI Google search)
3. **Citation extraction** — parse the response HTML/markdown for source links, normalize hosts, classify as own/competitor/3rd-party
4. **Snapshot storage** — JSON per (date, engine, query) in `reports/ai-citations/`
5. **Diff report** — week-over-week change in citation share, new mentions, lost mentions, competitor delta

## What this skill does

1. **Initialize topic clusters** from `config/clusters.yml` (or interactive prompt)
2. **Issue queries** to each engine
   - Playwright for ChatGPT (with login cookie kept in `~/.config/ai-tracker/chatgpt-cookie.json`)
   - REST for Perplexity (API key in env)
   - REST for Gemini (Google AI Studio API key)
   - SerpAPI Google search with `ai_overview=true` parameter
3. **Extract citations** — host, URL, title, position in response
4. **Compute metrics**:
   - **Citation share**: % of queries that mention the brand
   - **Citation depth**: average position when mentioned
   - **Competitor delta**: own vs top-3 competitors' citation share
5. **Persist** snapshot + run delta vs last week's snapshot
6. **Report** — markdown summary with sparklines, alerts for citation loss

## Critical rules (enforced)

- Respect rate limits per engine (ChatGPT: 10 queries/hour, Perplexity: 60/min, Gemini: 60/min)
- Never store the LLM responses themselves — only the extracted citations (privacy + storage)
- Anonymize the cookie/API key paths in reports — never echo them
- For Japanese queries, use kanji/kana/romaji variants where natural
- Persist `ai-citation-snapshot/v1`; reject answer/body/prompt/cookie/key/token/secret fields recursively
- Every observation must name the canonical `targetId` and tested `variantId`.
  Same-condition repetition is identified by the engine/model/locale/variant
  tuple; do not add undeclared fields to the strict v1 artifact
- One successful run is `AI_CITED_VOLATILE`, never stable.
  `AI_CITED_STABLE` requires at least three successful repetitions under the
  same condition
- Use canonical target count—not wording-variant count—as the share denominator
- A branded-only sample is a measurement defect and cannot support overall
  share-of-voice claims
- `llms.txt` existence is not citation evidence. Only a validated engine
  observation snapshot can establish mention or citation status
- Keep AI citation, GSC search visibility, content readiness, and conversion
  measurement as separate status axes

## Usage patterns

### Pattern 1: Weekly automated run

GitHub Actions cron: every Monday 09:00 JST, run all clusters, post diff to Discord.

```yaml
- run: claude --skill netsujo-aio:ai-citation-tracker --args "run --clusters all --output reports/ai-citations/$(date -I).json"
```

### Pattern 2: Pre/post content publication

```
> /blog/bizdev-guide を retitle した。AI citation baseline 取得
```

Captures current citation state for "BizDev 京都", "事業開発 とは", "ビズデブ 役割" before content goes live. Re-run 14 days after deployment to measure lift.

### Pattern 3: Competitor benchmark

```
> "京都 IT 勉強会" cluster の競合 citation share を見る
```

Outputs a condition-scoped citation share with its canonical-target denominator,
plus competitor evidence and missing-coverage warnings. Never substitute sample
wording variants for independent targets.

## Output

```
{
  "contract": "ai-citation-snapshot/v1",
  "schemaVersion": 1,
  "snapshotId": "ai-YYYYMMDD-run",
  "siteId": "example",
  "observedAt": "2026-07-29T10:00:00.000Z",
  "status": "success",
  "observations": [
    {
      "targetId": "A-01",
      "observedAt": "2026-07-29T10:00:00.000Z",
      "variantId": "A-01-v1",
      "engine": "chatgpt",
      "model": null,
      "locale": "ja-JP",
      "runCount": 3,
      "successCount": 2,
      "ownMentionCount": 2,
      "ownCitationCount": 1,
      "ownCitationUrls": ["https://example.com/decision-page"],
      "competitorDomains": [],
      "stability": "volatile",
      "factCheck": "pass",
      "snapshotRef": "ai-YYYYMMDD-run"
    }
  ],
  "providerFailures": []
}
```

## References

- CMU GEO Framework: https://arxiv.org/abs/2311.09735
- SerpAPI AI Overview parameter: https://serpapi.com/blog/ai-overview-serp/
- Perplexity API: https://docs.perplexity.ai/
- Profound LLM citation tracker (commercial alternative): https://www.tryprofound.com/
- SE Ranking AI Visibility: https://seranking.com/ai-visibility-tracker.html (one-call covers 5 platforms)
