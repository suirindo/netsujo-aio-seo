---
name: pre-merge-test-suite
description: Orchestrate full test suite before merging any PR. Runs link-integrity-tester + content-fact-validator + schema-validator + build/lint/test in sequence, plus visual diff on changed routes. Must be run on every PR that modifies user-facing pages, schemas, or content data. Returns aggregated pass/fail report with merge recommendation. Use when user says "test before merge", "pre-merge", "test all", "徹底テスト", "merge前確認", or when about to claim "ready to merge".
---

# Pre-Merge Test Suite

Single entry point that runs all SEO-critical pre-merge tests in sequence and returns a unified verdict. Designed to be invoked before any "merge して" request.

## Why this matters

Real incidents on 2026-06-04:
1. **Fact propagation** — Fabricated lecture entry passed `npm run build` because builds don't validate facts
2. **Link mismatch** — `/blog`'s "全62記事を一覧で見る" pointed to `/archive` (event page); build had no way to detect intent mismatch
3. **Schema graft** — New Course schema component generated from incorrect input data; structurally valid but factually wrong

Three failures in one session. All would have been caught by orchestrating: build → fact-check → link-check → schema-check → visual diff. None were caught because there was no orchestrator.

## What this skill does

Runs the following stages **in order**. Failure at any stage blocks subsequent stages and reports the verdict.

### Stage 0: Static prerequisites
- `npm run build` exits 0
- `npm run lint` exits 0 (warnings OK, errors not)
- `tsc --noEmit` exits 0
- All affected file have valid syntax

### Stage 1: content-fact-validator
- Parse `git diff main` for factual claims in changed files
- Cross-reference against canonical sources (Strapi, official URLs)
- FAIL = block merge

### Stage 2: schema-validator
- All `<script type="application/ld+json">` blocks valid
- Graph integrity (`@id` references resolve)
- Required fields per Google Rich Results
- FAIL = block merge

### Stage 3: link-integrity-tester
- All internal `<Link>` / `<a>` in changed files resolve to existing routes
- Semantic intent matches destination
- OG images reachable
- WARN on cross-domain non-200 (might be SSO); FAIL on internal broken

### Stage 4: Visual rendering check
- Fetch each changed page (via Preview URL if available, else mock-build locally)
- Verify H1 / H2 visible, no overlapping elements, no monospace fonts (per `feedback_writing_rules.md`)
- Mobile 375px viewport check
- WARN on visual regressions

### Stage 5: Production reflection (post-merge)
- After merge, wait for Vercel deploy
- Compare changed pages' rendered HTML to expected
- Verify no stale CDN cache serving old content

## Critical rules (enforced)

- **Stage 1 (fact-check) MUST pass before merge** — facts cannot be fixed by ISR or re-deploy. Facts in deployed HTML reach Google/AI engines and get embedded in their training/index
- **Stage 2 (schema) MUST pass** — broken JSON-LD silently degrades SEO with no visible warning
- **Stage 3 (links) MUST pass** — broken/mismatched links are user-facing bugs
- **Stage 4 (visual) WARN → human review** — flag for designer review, don't auto-block
- **Stage 5 runs post-merge, NOT pre-merge** — pre-merge can't access merged state

## When this skill is required

**Always required** when the PR includes any of:
- Changes to `src/lib/authors-fallback.ts`, `community-stats-constants.ts`, `blog-data.ts`, content data files
- New or modified `*JsonLd` components, `<script type="application/ld+json">` blocks
- New or modified `<Link>` / `<a>` / `onClick={() => router.push}`
- New page routes
- `metadata.title` / `metadata.description` / `metadata.openGraph` changes
- `public/llms.txt` / `public/llms-full.txt` updates

**Optional but recommended** for:
- CSS/style-only changes
- Bug fixes that don't touch user-facing pages

## Usage

### Pattern 1: Before "merge して" request

```
> PR #109 を merge する前に pre-merge-test-suite
```

Suite runs all 5 stages, returns aggregated verdict. Only if all PASS, present "ready to merge" to owner.

### Pattern 2: Auto-trigger on commit

In a CI workflow, trigger this skill via webhook when a PR's HEAD updates.

### Pattern 3: After lessons-learned event

When a new lessons-learned doc is added, update this skill's stages to include detection for that specific failure mode.

## Output (success)

```
{
  "pr": "#109",
  "verdict": "PASS — ready to merge",
  "stages": {
    "build": { "pass": true, "duration_ms": 11000 },
    "fact_check": { "pass": true, "claims_validated": 8 },
    "schema": { "pass": true, "blocks_validated": 14 },
    "link_integrity": { "pass": true, "links_checked": 47 },
    "visual": { "pass": true, "pages_checked": 6, "warnings": 0 }
  },
  "merge_command": "gh pr merge 109 --squash --delete-branch"
}
```

## Output (failure)

```
{
  "pr": "#109",
  "verdict": "FAIL — do NOT merge",
  "blocked_at": "fact_check",
  "failures": [
    {
      "stage": "fact_check",
      "claim": "公立はこだて未来大学 登壇 (2025-05)",
      "from_file": "src/lib/authors-fallback.ts:91",
      "reason": "Strapi article shows different speaker (石田結花さん) and venue (大正大学京都アカデミア)",
      "action_required": "Remove this entry + downstream propagations before next merge attempt"
    }
  ],
  "must_fix_before_merge": true
}
```

## Composes with

- `link-integrity-tester` — Stage 3
- `content-fact-validator` — Stage 1
- `schema-validator` — Stage 2
- `h1-mobile-check` — Stage 4 mobile check
- `jp-ascii-space-fix` — Stage 4 text quality
- `gsc-weekly-audit` — Stage 5 production observation (post-merge)

## References

- 2026-06-04 lessons-learned (fabrication + link mismatch double incident)
- `feedback_verification.md`
- `feedback_review_gates.md`
