---
name: passage-citability-checker
description: Score the AI citation readiness of a page's opening passage. Measures definition density, sourced-statistic density, answer-first structure, entity clarity, and self-containedness, then proposes rewrites without claiming a citation lift. Use when user says "AI引用", "GEO", "AI Overview optimization", "ChatGPT citation", "passage citability", "AIに引用される", "冒頭リード", or "intro rewrite".
---

# Passage Citability Checker

Scores the opening passage of a blog/landing page on five retrieval-readiness
dimensions and outputs an actionable rewrite plan. The rubric is a local
editorial heuristic informed by the GEO research literature; it is not a
provider ranking model.

## Why this matters

- A self-contained opening passage is easier to retrieve and evaluate than an
  unsupported preamble, but this heuristic does not prove citation probability
- Google recommends standard SEO, helpful content, accessible text, and
  structured data consistency; no special AI-only markup guarantees inclusion
- Citation success must be measured separately with repeated, condition-scoped
  engine observations

## What this skill scores

For the page's first 200 tokens (lead paragraph + first H2/H3 if reached):

| Dimension | Weight | What it measures |
|---|---|---|
| **Definition density** | 25% | Is there a "Xとは Y である" / "X is Y" sentence in the first 3 sentences? |
| **Statistic density** | 20% | Count of concrete numbers (years, percentages, counts) per 100 tokens |
| **Answer-first structure** | 19% | Does the first sentence directly answer the implied query, or does it preamble? |
| **Entity clarity** | 16% | Are proper nouns (brand, place, person, technology) introduced with full names + parenthetical reading? |
| **Citation hooks** | 20% | Presence of quote-friendly fragments (e.g., "3つの理由", "ステップ1〜5", "A vs B comparison") |

Total score 0-100. Local editorial threshold:
- 80+: Strong content readiness
- 60-79: Acceptable, room for improvement
- <60: Rewrite candidate

## What this skill does

1. **Fetch the target URL** (HTML or local `.tsx`/`.mdx` file). For client-side rendered pages, use Playwright with `wait_for_idle`
2. **Extract the lead passage** — first paragraph after `<h1>`, capped at 200 tokens (Japanese: count characters / 1.5)
3. **Tokenize + analyze** — sentence segmentation, NER for entities (using simple regex heuristics for Japanese: proper noun patterns + parenthetical readings)
4. **Score on 5 dimensions** and compute weighted total
5. **Generate rewrite proposal** — if score < 80, propose:
   - Add a "Xとは Y である" sentence at position 1
   - Surface concrete numbers only when already supported by a canonical source
   - Reorder to put the answer first
   - Add (parenthetical reading) for proper nouns
6. **Report** — current score, diagnosis, proposed rewrite, expected score after rewrite

## Critical rules (enforced)

- Respect `feedback_no_japanese_ascii_space.md` — no half-width spaces between JP and ASCII in proposals
- Respect `feedback_writing_rules.md` — ですます調, no "思い"/"考え"/"のが"
- Don't propose rewrites that change factual claims — only structural reordering
- For Web3/AI/legal/medical content (YMYL), preserve all caveats and source citations in the original passage

## Usage patterns

### Pattern 1: Audit a single page

```
> /blog/bizdev-guide の冒頭を citability check して
```

Output: dimension scores, current 62/100, rewrite proposal that brings it to 86/100.

### Pattern 2: Batch audit the top-impressions pages

```
> GSC 上位10ページの冒頭をすべて citability check して
```

Pulls GSC top pages, audits each, returns prioritized rewrite list (lowest score = highest priority).

### Pattern 3: Pre-publish check in CI

GitHub Actions hook: any new `.tsx` under `src/app/blog/` must score >= 70 to merge.

## Output

```
{
  "url": "https://netsujo.jp/blog/bizdev-guide",
  "lead_passage": "...",
  "scores": {
    "definition_density": 18,    // out of 25
    "statistic_density": 8,      // out of 20
    "answer_first": 14,          // out of 19
    "entity_clarity": 12,        // out of 16
    "citation_hooks": 10         // out of 20
  },
  "total": 62,
  "verdict": "Acceptable, room for improvement",
  "rewrite_proposal": "BizDev(ビズデブ・事業開発)とは、技術製品やサービスの市場拡大を担う職種です。営業との違いは...(再構成済み)",
  "expected_score_after": 86,
  "measurement_plan": "capture a pre-change snapshot and repeat the same engine/model/locale/variant conditions after release"
}
```

## Evidence and outcome boundary

- This score is `contentReadiness`, not an AI citation status.
- Never emit an estimated citation-lift percentage from the rubric score.
- Check every mutable fact against its canonical snapshot before recommending
  it as a citation hook. A mismatch is `AI_FACT_CONFLICT`.
- `llms.txt` or schema presence is delivery evidence only.
- A citation is stable only after at least three successful same-condition
  observations; one citation remains volatile.

## References

- CMU GEO Framework: https://arxiv.org/abs/2311.09735 (Aggarwal et al. "GEO: Generative Engine Optimization")
- Search Engine Land GEO 2026 完全ガイド: https://searchengineland.com/mastering-generative-engine-optimization-in-2026-full-guide-469142
- Google公式 AI Optimization Guide: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Sapt AI Search Optimization 2026: https://sapt.ai/insights/ai-search-optimization-complete-guide-chatgpt-perplexity-citations
