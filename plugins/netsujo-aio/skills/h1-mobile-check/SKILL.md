---
name: h1-mobile-check
description: Detect Japanese H1 headings that break awkwardly on mobile (375px), where 1-2 characters spill onto a second line or particles/verbs get split mid-phrase. Renders the page at iPhone SE width, measures line boxes, and suggests optimal `<br />` insertion points using bunsetsu boundaries. Battle-tested on netsujo.jp and miyakodeit.com (3 prior incidents). Use when user says "H1", "mobile break", "見出し改行", "375px", "Japanese line break", "iPhone改行", "H1モバイル", or "見出しが崩れる".
---

# H1 Mobile Break Checker

Production-ready checker for Japanese H1/H2 headings that detects mid-particle splits, dangling tail characters, and over-long headings at 375px mobile width. Combines static analysis (character count + grammar) with dynamic Playwright rendering (actual line-box measurement) and proposes `<br />` insertions at natural bunsetsu boundaries.

## What it does

1. **Static H1/H2 extraction** from `.tsx`, `.jsx`, `.html`, `.md`, `.mdx` files or live URLs
2. **Length check**: warns when H1 exceeds 15 characters (will likely wrap on 375px)
3. **Dynamic measurement**: renders the page at 375x667 with Playwright, reads `getBoundingClientRect()` per line, flags tail lines under 3 characters
4. **Particle-split detection**: flags Critical when a line starts with a Japanese particle (`を`, `が`, `に`, `で`, `と`, `は`, `から`, `まで`, `より`, `へ`, `の`)
5. **Verb-stem-split detection**: flags Warning when a verb is broken between stem and ending (e.g. `もたら` + `す`)
6. **`<br />` suggestion**: analyzes bunsetsu boundaries and proposes the optimal insertion point so both halves are visually balanced and grammatically intact

## When to use

- Before every deploy that touches H1/H2 copy
- After translating English headings into Japanese
- When auditing existing blog/marketing pages for mobile UX regressions
- In CI as a gate against H1 length regressions

## Critical rules (enforced)

Per the netsujo monorepo `CLAUDE.md` headline rules:

1. **No 1-2 character tail lines** — the final wrapped line must contain at least 3 characters of meaningful content
2. **No particle at line head** — `を/が/に/で/と/は/から/まで/より/へ/の` must never start a wrapped line
3. **No verb stem/ending split** — `もたらす`, `はじまる`, `つくる` must stay together
4. **H1 length 15 chars or fewer** (recommended); 16-22 acceptable only with explicit `<br />`
5. **Sub-titles belong in a separate `<p>`** — never concatenated into H1 with `—` or `:`

This skill enforces all 5 at check time.

## Usage

### Check a live URL

```bash
python3 scripts/h1-mobile-check.py --url https://netsujo.jp/blog/ai-blockchain
```

Console output:

```
H1: AI×ブロックチェーンが企業にもたらす5つの変革 (20 chars)
  [Critical] Tail line "す5つの変革" splits verb もたらす
  [Suggestion] Insert <br /> after もたらす:
    AI×ブロックチェーンが企業に<br />もたらす5つの変革
```

### Check a single source file

```bash
python3 scripts/h1-mobile-check.py --file app/blog/[slug]/page.tsx
```

Extracts every `<h1>` and `<h2>` via regex/AST and runs both static and dynamic checks (dynamic only if `--url` base is also given).

### Batch scan a directory

```bash
python3 scripts/h1-mobile-check.py --batch ./app --report report.md
```

Outputs a Markdown report grouped by file with Critical/Warning columns.

### Suggest a `<br />` for a raw string

```bash
python3 scripts/h1-mobile-check.py --suggest "AI×ブロックチェーンが企業にもたらす5つの変革"
```

Output:

```
Original (20 chars):
  AI×ブロックチェーンが企業にもたらす5つの変革

Recommended break (balance: 12 / 8):
  AI×ブロックチェーンが企業に<br />もたらす5つの変革

Alternative (balance: 14 / 6):
  AI×ブロックチェーンが企業にもたらす<br />5つの変革
```

## Detection logic

| Layer | Tool | Catches |
|---|---|---|
| Static | regex + length count | H1 > 15 chars, sub-title concat with `—` or `:` |
| Grammar | particle/verb dictionary | particle-first line, verb stem split |
| Dynamic | Playwright @ 375x667 | actual wrapped tail < 3 chars, total lines > 2 |
| Suggestion | bunsetsu segmentation | optimal `<br />` index (balance closest to 50/50) |

Playwright is an **optional dependency**. Without it the skill falls back to static + grammar only, which already catches the 3 historical incidents below.

## Battle-tested incidents

This skill exists because of three confirmed production regressions:

- **2026-04-08 (miyakodeit blog)**: H1「AI×ブロックチェーンが企業にもたらす5つの変革」(20文字)がモバイル375pxで「す5つの変革」だけが次行に落ちた。動詞「もたらす」が分断され、可読性が著しく低下。→ `<br />`を「企業に」の後に手動挿入して解消
- **2026-04-08 (miyakodeit blog)**: H1「自治体×Web3の実証実験ガイド — 活用領域・進め方・成功のポイント」(33文字)がモバイルで3行に崩れた。サブタイトルをH1にconcatしたことがroot cause。→ サブタイトルを`<p className="subtitle">`に分離して解消
- **2026-05-26 (netsujo.jpランディング)**: H1「京都でIT勉強会・エンジニア交流会を探している方へ」(22文字)が「を探」位置で改行され、助詞「を」が次行頭にきた。→ `<br />`を「エンジニア交流会を」の後に挿入して解消

These three failures define the default rules: **15-char soft limit**, **particle-head Critical**, **verb-split Warning**.

## CLI reference

```
python3 h1-mobile-check.py --url <URL>            # live page check
python3 h1-mobile-check.py --file <path>          # single file static check
python3 h1-mobile-check.py --batch <dir>          # recursive scan
python3 h1-mobile-check.py --suggest <text>       # br insertion suggestion
python3 h1-mobile-check.py --report <path.md>     # write markdown report
python3 h1-mobile-check.py --viewport 375x667     # override viewport
python3 h1-mobile-check.py --max-chars 15         # override length threshold
python3 h1-mobile-check.py --strict               # fail on Warning, not just Critical
```

Exit codes: `0` clean, `1` Warning only, `2` Critical present.

## Output format

Console: colored table (red=Critical, yellow=Warning, green=clean) grouped by file/URL.

Markdown report (`--report`):

```markdown
# H1 Mobile Check Report

## Summary
- Pages scanned: 12
- Critical: 2
- Warnings: 4

## /blog/ai-blockchain
- **Critical**: 助詞「を」が行頭 (line 2)
- **Suggestion**: `<br />` after 「企業に」
```

## Configuration

| Setting | Default | Description |
|---|---|---|
| Viewport width | 375px | iPhone SE / smallest common mobile |
| Viewport height | 667px | matches iPhone SE |
| Max H1 chars | 15 | Warning threshold |
| Min tail chars | 3 | Critical if wrapped tail < this |
| Particle list | `を が に で と は から まで より へ の` | line-head ban list |
| Strict mode | false | treat Warning as failure |
| Playwright | auto | falls back to static-only if missing |

## Reference files

- `references/japanese-line-break-rules.md` — 禁則処理 (kinsoku), 助詞一覧, 文節区切り, `<br />` 挿入アルゴリズム
- `scripts/h1-mobile-check.py` — Checker + suggestion engine

## Related skills

- `netsujo-aio:jsonld-article` — Article schema (often touched on the same PR)
- `claude-seo:seo-page` — Single-page SEO audit (covers H1 from SEO angle, not layout)
- `claude-seo:seo-technical` — Core Web Vitals (CLS regressions from H1 wrap)
