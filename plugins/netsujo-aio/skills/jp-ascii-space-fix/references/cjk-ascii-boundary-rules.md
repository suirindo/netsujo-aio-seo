# CJK↔ASCII Boundary Rules

Reference tables and rationale for the `jp-ascii-space-fix` skill. Keep this file in sync with `scripts/jp-ascii-space-fix.py` — the regex constants are the source of truth, this file explains them.

## Unicode ranges treated as CJK

| Block | Range | Examples |
|---|---|---|
| Hiragana | U+3040–U+309F | あ い う え お ん |
| Katakana | U+30A0–U+30FF | ア イ ウ エ オ ン ー |
| CJK Unified Ideographs | U+4E00–U+9FFF | 日 本 語 京 都 |
| Halfwidth and Fullwidth Forms | U+FF00–U+FFEF | ＡＢＣ １２３ ｱｲｳ |

Not currently included (out of scope for this skill):

- CJK Compatibility Ideographs (U+F900–U+FAFF) — rare, mostly historical
- CJK Extension A/B/C/D/E/F (U+3400–U+4DBF, U+20000+) — rare in modern web copy
- Kanbun, Bopomofo, Hangul — non-Japanese CJK scripts

If a project needs them, extend `CJK_CLASS` in the script.

## ASCII ranges and punctuation sets

The two ASCII classes are deliberately asymmetric so closing punctuation on the left and opening punctuation on the right are caught:

| Side | Class | Rationale |
|---|---|---|
| Left of space (preceding ASCII) | `[A-Za-z0-9_.\)\}\]>]` | Catches `Next.js ` (period), `(API) ` (close paren), `<tag> ` (close angle) before a CJK char |
| Right of space (following ASCII) | `[A-Za-z0-9_\(\{\[<]` | Catches ` (API`, ` <tag`, ` {value` after a CJK char |

Underscore is included because it appears in identifiers (`schema_org`).

## Spaces that MUST be preserved

| Context | Example | Why |
|---|---|---|
| ASCII + space + ASCII | `PR #63`, `Next.js 15`, `Node.js v20` | Both sides ASCII — not a boundary |
| Markdown unordered list | `- 項目`, `* 項目`, `+ 項目` | List grammar |
| Markdown ordered list | `1. 項目`, `12) 項目` | List grammar |
| Markdown heading | `# 見出し`, `## 見出し`, `###### 見出し` | Heading grammar |
| Markdown blockquote | `> 引用`, `>> 二重引用` | Blockquote grammar |
| Markdown table separator | `| 列 |` | Table grammar |
| Fenced code block content | between matching ``` or ~~~ | Verbatim |
| Inline code | `` `Next.js` ``, `` `useState` `` | Verbatim |
| Front-matter | YAML between `---` ... `---` | YAML grammar |
| HTML attribute value | `<img alt="日本語 と English">` | Inside quoted attribute |
| JS/TS comment | `// 日本語 comment` | Comment grammar |

The skill detects each of these and masks the region before running the boundary regexes.

## Spaces that MUST be removed

| Pattern | Bad | Good |
|---|---|---|
| ASCII word + Japanese particle | `Next.js は速い` | `Next.jsは速い` |
| Japanese verb + ASCII identifier | `を Vercel に` | `をVercelに` |
| Number + Japanese unit | `15 個` | `15個` (note: also handle 15個 vs 15 個 unit-spacing convention if project requires) |
| Close paren + Japanese | `(API) を呼ぶ` | `(API)を呼ぶ` |
| Japanese + open angle | `タグ <div>` | `タグ<div>` |
| Identifier + Japanese | `useState の戻り値` | `useStateの戻り値` |

## perl one-liner vs Python skill

The original 2026-05-27 PR #67 sweep used:

```bash
perl -CSDA -i -pe 's/([A-Za-z0-9])\s+([\x{3040}-\x{30ff}\x{4e00}-\x{9fff}])/$1$2/g; s/([\x{3040}-\x{30ff}\x{4e00}-\x{9fff}])\s+([A-Za-z0-9])/$1$2/g' **/*.{md,tsx,ts}
```

This worked for 150 files in one pass but had three failure modes that this skill fixes:

| Failure mode | perl one-liner | Python skill |
|---|---|---|
| Rewrites inside fenced code blocks | Yes (broke `npm install foo` style samples) | No — fenced regions are masked |
| Rewrites inside HTML/JSX attribute values | Yes (broke `alt="..."` with intentional spacing) | No — attribute values are masked |
| Rewrites inline code spans | Yes (broke `` `Next.js` の `` examples) | No — inline code is masked |
| Reports per-file/per-line counts | No (silent edit) | Yes — line:column diff in dry-run |
| Git-scoped runs | Manual `git diff --name-only \| xargs` | Native `--git-staged` / `--diff` |
| Pre-commit hook integration | Awkward | Exit code 1 on dry-run match |
| CI machine-readable output | None | `--json` |

The perl one-liner is still useful for a fresh repository where every file should be swept. The skill is the right tool for ongoing maintenance, CMS-imported content, and pre-commit gating.

## Edge cases to be aware of

- **Em dashes and en dashes**: `—` (U+2014), `–` (U+2013) are not ASCII and not CJK. Spaces around them are left alone.
- **Middle dot `・`** (U+30FB): treated as CJK (in Halfwidth and Fullwidth Forms block extension); space around it is removed.
- **Fullwidth digits `０-９`** (U+FF10–U+FF19): treated as CJK. `Next.js　１５` (with fullwidth space) is out of scope — only ASCII space U+0020 is touched.
- **Non-breaking space ` `**: out of scope by default. Add to the pattern if a project uses NBSP intentionally.
- **Zero-width characters (`​`, `‌`, `‍`)**: left alone. Some teams insert ZWSP as a typography hint — that is the alternative to space removal, not a target for removal.
