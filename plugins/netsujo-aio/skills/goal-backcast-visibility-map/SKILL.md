---
name: goal-backcast-visibility-map
description: Build or validate a versioned search and AI visibility target registry by backcasting from an approved business goal, decision, conversion, destination, evidence, and measurement path. Use for "visibility map", "検索需要マップ", "AI質問設計", "goal backcast", "検索・AI可視性", or when joining GSC query/page and AI citation snapshots without collapsing their statuses.
---

# Goal-backcast Visibility Map

Generate decision-ready targets from business outcomes. Do not start from traffic
volume or a generic keyword list.

## Required reasoning order

1. **Goal** — revenue, qualified lead, participation, continued contact,
   partnership, or earned citation.
2. **Actor** — the person who must decide.
3. **Decision** — the decision immediately before the conversion.
4. **Conversion** — event/destination and qualification/exclusion rules.
5. **Question** — keep short search keywords separate from conversational
   questions.
6. **Evidence** — first-party proof and canonical source.
7. **Destination** — owning URL, supporting URL, CTA, and measurement key.
8. **Baseline** — GSC query/page, SERP spot check, AI citation snapshot, and
   content readiness remain independent axes.
9. **Gap** — retrieval, trust, comparison, action, or measurement.
10. **ChangeSpec** — cause, change, owner, completion criterion, verification,
    and 7/28/90-day loop.

## Priority contract

Assign P0/P1/P2 from all five factors: business value, intent strength,
site-specific evidence, implementation feasibility, and measurability.

- A high-volume generic term far from the approved decision cannot outrank a
  lower-volume commercial term connected to the primary conversion.
- A target without Goal → Decision → Conversion references is a proposal, not
  a confirmed P0.
- `impressions=0` is a measured search result, not proof of non-indexation.
- One SERP spot check without the domain is `SEARCH_UNMEASURED` until query-level
  GSC or another repeatable source is available. Never label it "圏外".

## Clustering and cannibalization

- One canonical target owns natural wording variants. Store the canonical
  target ID plus variant IDs; do not count suffix/politeness variants as
  independent observations.
- Every AI observation carries `targetId`, `variantId`, and a same-condition
  identity. Citation rate denominators use canonical targets, not raw variants.
- Classify branded and non-branded targets separately. A branded-only sample is
  a major measurement defect and cannot support an overall citation-share
  claim.
- When an article and service page compete for the same commercial intent,
  inspect GSC query/page rows, name one primary decision page, name the other
  supporting education content, and specify internal-link/canonical roles.

## Status axes

Never collapse search, AI citation, content readiness, and CV measurement into
one status.

- Search: `SEARCH_OWNED`, `SEARCH_VISIBLE`, `SEARCH_EMERGING`,
  `SEARCH_CTR_GAP`, `SEARCH_PAGE_MISMATCH`, `SEARCH_CONTENT_GAP`,
  `SEARCH_UNMEASURED`.
- AI: `AI_CITED_STABLE`, `AI_CITED_VOLATILE`,
  `AI_MENTION_NO_CITATION`, `AI_NOT_CITED`, `AI_ANSWER_READY`,
  `AI_CONTENT_PARTIAL`, `AI_CONTENT_GAP`, `AI_FACT_CONFLICT`,
  `AI_UNMEASURED`.

One successful citation run is never stable. Stable requires at least three
successful repeat observations under the same engine/model/locale/variant
condition. Mixed results are volatile.

## Fact and measurement gates

- A current-value mismatch across page copy, JSON-LD, metadata, llms files,
  partner-site copy, or dynamic UI is `AI_FACT_CONFLICT`; stop citation/content
  expansion until resolved.
- Historical publication-time values remain historical when the surrounding
  passage and date make that meaning explicit. Do not rewrite them to current
  values.
- `llms.txt` existence is a delivery fact, never evidence of a mention or
  citation. Citation success requires an engine observation snapshot.
- Seed-only UI is `unmeasured`. It must not pass a readiness gate that requires
  GSC/AI imports.
- `null` means unmeasured/unavailable; numeric zero means a successful
  measurement of zero.

## Output contracts

Use the exact versioned contracts under `schemas/`:

- `visibility-targets/v1`
- `ai-citation-snapshot/v1`
- `community-stats-snapshot/v1`
- `visibility-dashboard-import/v1`

Reject unsupported versions, duplicate IDs, orphan Goal references, forbidden
answer/cookie/key fields, and snapshots whose count breakdown does not balance.
Output JSON only when the caller asks for an import artifact.

## Community statistics lineage

For current mutable statistics, validate the entire lineage:

`paginated upstream adapter → versioned count rule → validated immutable success snapshot → atomic publisher → pinned consumers`

Required behavior:

- Fetch every upstream page; a partial pagination result fails refresh.
- Apply `connpass-published-events-v1`: count unique published group events in
  completed, cancelled, and upcoming states; exclude private/unpublished and
  duplicates; classify dates in JST.
- On timeout, 429, or 5xx, do not publish zero or a constant. Serve the
  last-known-good snapshot and record freshness plus a safe error type in the
  separate refresh-state/public envelope. The immutable success snapshot
  itself is never rewritten to `stale`.
- Pin one snapshot ID at build start. Every artifact in that build uses the
  pinned payload even if a newer snapshot is published concurrently.
- All consumers display/verify the same snapshot ID. Equal numeric values with
  different snapshot IDs are a provenance mismatch.
- Current-value literals in consumers fail CI; only named historical fixtures
  may contain literal historical counts.

## ChangeSpec for pipeline conflicts

If values happen to match but consumers fetch upstream independently, aggregate
twice, use constant fallback, apply different stale thresholds, or show
different snapshot IDs, emit `FACT_PIPELINE_CONFLICT`. The remediation must name
the canonical source, single fetch owner, versioned snapshot, last-known-good
fallback, atomic publish boundary, and regression tests. "Replace the number"
is not a sufficient remediation.

## Validation

From the plugin repository root:

```bash
python3 scripts/validate-contracts.py
python3 scripts/run-evals.py
```

All E-01 through E-18 must pass before publishing the plugin.
