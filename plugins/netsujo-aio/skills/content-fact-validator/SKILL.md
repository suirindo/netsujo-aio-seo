---
name: content-fact-validator
description: Use when user says "fact check", "事実確認", "原典確認", "verify claim", "propagate data", or BEFORE editing achievements/awards/lectures/affiliations/bios/statistics in authors-fallback.ts, site-facts.ts, community-stats-constants.ts, Person/Course/Organization schemas, or any copy that states facts about people or organizations. Also use when copying "existing" data from one file into a new page or schema — existing data is NOT presumed verified.
---

# Content Fact Validator

Validates factual claims before they propagate. Specifically targets the failure mode where pre-existing data in `authors-fallback.ts`, `community-stats-constants.ts`, or content data files is treated as "already verified" and amplified into new pages/schemas — but was actually fabricated or outdated.

## Why this matters

Real incident on 2026-06-04: `src/lib/authors-fallback.ts` contained an entry "生成AI×エンジニアの未来 公立はこだて未来大学 登壇 (2025-05)" listing 飯田友広 as the speaker at 公立はこだて未来大学. When I rewrote `bio`, added entries to `/founder` achievements, and created `CourseListJsonLd`, I propagated this entry into 3+ new locations. The owner discovered it because they never gave a lecture there.

The real venue was 大正大学京都アカデミア (a Kyoto campus of 大正大学, completely unrelated to 公立はこだて未来大学). The actual speaker was 石田結花さん (community member). The actual date was 2025-05-14 (Strapi article had a typo 2024-05-14). Four factual errors in one entry, undetected by build/lint/test.

**Root cause: "existing data is presumed correct" is a dangerous assumption when the data was entered by someone else without source links.**

## What this skill checks

For each factual claim being added or propagated:

1. **Source attribution** — Does the entry have a `source_url` field or comment pointing to canonical source?
2. **Strapi cross-reference** — If the claim relates to a blog post topic, find the Strapi article and compare key facts (date, organization, role)
3. **External canonical check** — For external entities (universities, companies, events), fetch the official URL and verify name/existence
4. **connpass / event page** — If the claim is about an event, find the connpass / Doorkeeper / official event page and verify date/speaker
5. **Geographic plausibility** — If a person's activities cluster in one region, flag entries from geographically distant locations (e.g., a 京都-centered figure having activity in 函館 is suspicious)
6. **Temporal coherence** — Dates align with adjacent activities; no future claims or impossibly old entries

## Patterns specifically flagged

- **achievements / awards / speaking entries** lacking `source_url` or reference comment
- **Bio strings** listing multiple organizations where one is geographically/temporally outlier
- **Person schema's `performerIn` / `award`** entries with provider names that don't appear elsewhere in the codebase or Strapi
- **Course / Educational schema** with `provider` university names not corroborated by Strapi articles
- **Statistics / counts** (member counts, event counts, years operating) that conflict with the canonical constants file
- **Dates** that don't match Strapi article's `displayDate` or excerpt text

## What this skill does

1. **Parse the change** (git diff or proposed write) to extract new factual claims
2. **For each claim, determine the appropriate canonical source**:
   - Netsujo 社の事実（役職・登記・認証・R&D状態） → `netsujo-web` の `site-facts.ts`（`check:facts` CI）+ memory `project_netsujo_confirmed_facts.md`
   - みやこでIT の事実（発足年・会場・統計） → `community-stats-constants.ts` + memory `project_miyakodeit_confirmed_facts.md`
   - Speaker / lecture → Strapi article search via slug heuristic + Web search
   - Award → official issuing org URL
   - Company/Organization affiliation → official membership page or press release
   - 人物の経歴・資格 → 本人確認または一次出典が無ければ**書かない**（memory `feedback_no_fabricated_credentials.md` / 2026-06-18「代表が元医師」虚偽事故）
3. **Fetch the canonical source** (WebFetch / Strapi API)
4. **Compare claim vs. source** on key fields
5. **Output** — for each claim: PASS (with source URL), WARN (couldn't verify), or FAIL (mismatch detected)
6. **If FAIL** — block the propagation, require source-corrected entry or removal

## Critical rules (enforced)

- **Build / lint / tsc do NOT validate facts**. They validate syntax. Facts must be human-attested or source-attested
- **No "既存だから正しい"**. Every propagation of pre-existing data into a new schema/page requires re-verification
- **When in doubt, ask the owner**. AI cannot reliably attest to a person's lecture history; the owner can
- **Geographic outliers are red flags**. Flag entries that don't fit the entity's regional pattern
- **Strapi articles are the canonical truth for blog-related facts**. If the claim relates to a topic with a blog post, the post's content (excerpt, displayDate, body text) is the source of record

## Usage

### Pattern 1: Before editing authors-fallback.ts

```
> authors-fallback.ts に achievements を追加したい。content-fact-validator で原典確認
```

Validator extracts the proposed entries, looks for Strapi articles matching each title/organization, returns a fact-check report.

### Pattern 2: Before propagating bio to new bio strings

```
> /community / /founder / Person schema に新しい bio を反映する前に content-fact-validator
```

Validator cross-references each factual claim in the bio against canonical sources.

### Pattern 3: After discovering an error

```
> 公立はこだて未来大学の捏造データを発見。全リポで残存していないか content-fact-validator
```

Validator grep-searches all repos for the false claim, generates a removal action list with exact file:line.

## Output

```
{
  "claims_checked": 13,
  "passes": 9,
  "warnings": 2,
  "failures": [
    {
      "claim": "公立はこだて未来大学 登壇 (2025-05)",
      "found_in": ["netsujo-web/src/lib/authors-fallback.ts:91-95", "miyakodeit/app/founder/page.tsx:34"],
      "canonical_source_searched": "Strapi article news-generative-ai-engineer-future-university-talk",
      "verdict": "FAIL",
      "actual_per_source": {
        "venue": "大正大学京都アカデミア",
        "speaker": "石田結花さん",
        "date": "2025-05-14",
        "role": "コミュニティ主催の勉強会・大学講義ではない"
      },
      "suggested_fix": "Remove this entry entirely from authors-fallback.ts and all downstream propagations",
      "owner_attest_required": true
    }
  ]
}
```

## References

- 2026-06-04 lessons-learned: `.company/lessons-learned/2026-06-04-hakodate-future-univ-fabrication.md`
- `memory/feedback_fact_check_required.md` (本 skill 制定により射程拡張)
- `.company/protocols/external-citation-protocol.md`
