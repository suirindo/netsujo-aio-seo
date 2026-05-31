---
name: jp-ascii-space-fix
description: Detect and remove half-width spaces at ASCII↔CJK boundaries in Markdown, TSX/TS/JSX/JS, HTML, JSON-LD, and plain text. Context-aware — skips fenced code blocks, HTML attributes, and ASCII-only runs. Battle-tested across netsujo-web (178 files, 1500+ replacements in lib/blog-data.ts alone). Use when user says "half-width space", "CJK space", "Japanese typography", "和欧混植", "ASCII boundary", "英単語と日本語のスペース", or "remove space between English and Japanese".
---

# JP ASCII↔CJK Space Fixer

Context-aware detector and remover of half-width spaces between ASCII characters (A-Z, a-z, 0-9, common punctuation) and CJK characters (Hiragana, Katakana, CJK Unified Ideographs, Halfwidth/Fullwidth Forms). Replaces one-off `perl -pi -e` sweeps with a skill that understands fenced code, HTML attributes, and Markdown list markers.

## What it does

1. **Scans files recursively** for the two boundary patterns (ASCII+space+CJK and CJK+space+ASCII)
2. **Skips contexts where the space is intentional**: fenced code blocks (```), inline code (`` ` ``), HTML attribute values, ASCII-only runs, Markdown list/heading/blockquote markers
3. **Reports** every match as `file:line:column` with before/after diff
4. **Applies fixes** only when `--apply` is explicitly passed (dry-run is default)
5. **Supports git scoping**: `--git-staged` for staged hunks only, `--diff <range>` for branch diffs

## When to use

- User says "half-width space", "CJK space", "Japanese typography", "和欧混植", "ASCII boundary"
- Cleaning up imported CMS content (Strapi rich text, MicroCMS, Google Docs export)
- Pre-commit hook to enforce repo-wide typography consistency
- Migrating legacy content that mixed `Next.js 15` style (good) with `Next.js のフレームワーク` (bad, space between `15` and `の`)
- Before deploying SEO-sensitive pages — Google indexes `ASCII+space+CJK` and `ASCII+CJK` as different tokens, so inconsistent source strings split ranking signal

## Why source-level removal, not CSS

Browsers can shape inter-script spacing at render time via:

- CSS `text-spacing-trim: space-all` (CSS Text Module Level 4, partial browser support as of 2026-05)
- OpenType `palt` / `halt` features on Japanese fonts
- JavaScript libraries like `pangu.js`

These belong in the rendering layer. The **source string** should be free of inter-script spaces because:

1. Google tokenizes the raw text. `エンジニア OS` and `エンジニアOS` produce different n-grams and different SERP eligibility.
2. JSON-LD `description`, `name`, OG tags, and `<title>` are read by crawlers without CSS applied.
3. Search-and-replace, grep, diff, and translation memory tools break when the same word appears with and without surrounding spaces.
4. Copy-paste from rendered HTML preserves the source string, so the typo propagates.

CSS makes it *look* right. The skill makes it *be* right.

## Boundary patterns

The two regexes that trigger detection (PCRE, multi-line off):

```
[A-Za-z0-9_.\)\}\]>] [\x{3040}-\x{30ff}\x{4e00}-\x{9fff}\x{ff00}-\x{ffef}]
[\x{3040}-\x{30ff}\x{4e00}-\x{9fff}\x{ff00}-\x{ffef}] [A-Za-z0-9_\(\{\[<]
```

Unicode ranges covered:

| Range | Block |
|---|---|
| U+3040–U+309F | Hiragana |
| U+30A0–U+30FF | Katakana |
| U+4E00–U+9FFF | CJK Unified Ideographs |
| U+FF00–U+FFEF | Halfwidth and Fullwidth Forms |

## Preserved spaces (false-positive guards)

| Pattern | Example | Reason |
|---|---|---|
| ASCII + space + ASCII | `PR #63`, `Next.js 15` | Both sides ASCII — not a boundary |
| Markdown list marker | `- 項目`, `* 項目`, `1. 項目` | Required by Markdown grammar |
| Markdown heading | `# 見出し`, `## 見出し` | Required by Markdown grammar |
| Blockquote | `> 引用` | Required by Markdown grammar |
| Fenced code block | ```` ```ts ... ``` ```` | Code is verbatim |
| Inline code | `` `Next.js` の `` | Inline code is verbatim |
| HTML attribute | `<a href="..." title="日本語">` | Inside quoted attribute |
| Front-matter | `--- ... ---` at top of `.md` | YAML grammar |

## Usage

### Scan a directory (dry-run, default)

```bash
python3 scripts/jp-ascii-space-fix.py --scan .
```

Output:

```
docs/blog/post-1.md:12:8: "Next.js は" → "Next.jsは"
docs/blog/post-1.md:34:22: "を Vercel に" → "をVercelに"
lib/blog-data.ts:1024:15: "Strapi の" → "Strapiの"
---
Files scanned: 421
Files with matches: 38
Total matches: 612
Run with --apply to rewrite.
```

### Apply fixes

```bash
python3 scripts/jp-ascii-space-fix.py --scan ./docs/ --apply
```

### Single file

```bash
python3 scripts/jp-ascii-space-fix.py --file README.md --dry-run
```

### Git-staged only (pre-commit)

```bash
python3 scripts/jp-ascii-space-fix.py --git-staged --apply
```

### Branch diff only

```bash
python3 scripts/jp-ascii-space-fix.py --diff origin/main..HEAD
```

## File types handled

| Extension | Parser |
|---|---|
| `.md`, `.mdx` | Markdown (fenced code, inline code, front-matter, list markers stripped) |
| `.tsx`, `.ts`, `.jsx`, `.js` | JS/TS string literals + JSX text nodes (template strings, double/single quoted) |
| `.html`, `.htm` | Text nodes only — attribute values skipped |
| `.json` | String values (treats JSON-LD `description`, `name` as text) |
| `.txt` | Plain text |
| `.yaml`, `.yml` | String values |

## CLI

```
python3 jp-ascii-space-fix.py [--scan DIR | --file FILE | --git-staged | --diff RANGE]
                              [--apply] [--dry-run] [--include GLOB] [--exclude GLOB]
                              [--no-color] [--json]
```

| Flag | Default | Description |
|---|---|---|
| `--scan PATH` | — | Recurse into directory |
| `--file PATH` | — | Single file |
| `--git-staged` | false | Restrict to staged hunks |
| `--diff RANGE` | — | Restrict to lines changed in git range |
| `--apply` | false | Actually rewrite files (default is dry-run) |
| `--include GLOB` | `*.md,*.tsx,*.ts,*.jsx,*.js,*.html,*.json,*.txt,*.yaml,*.yml` | Filter |
| `--exclude GLOB` | `node_modules/**,.next/**,dist/**,build/**,.git/**` | Skip |
| `--json` | false | Machine-readable output for CI |

Exit codes: `0` = no matches, `1` = matches found (dry-run), `2` = error.

## Battle-tested 事例

- **2026-05-24飯田指示**: 「英単語・半角数字と日本語全角文字の間に半角スペースを入れない」が明示的なルールとしてmemory化(`feedback_no_japanese_ascii_space.md`)
- **2026-05-26再指示**: ファイル修正だけでなくチャット応答テキストも対象。リポジトリ全体の未修正箇所を網羅する運用に格上げ
- **2026-05-27 PR #67**: netsujo-webリポで`perl -pi -e`一括置換を実行
  - 初版150ファイル変更
  - main merge後の再スキャンで28ファイル追加検出
  - 合計178ファイル
  - `lib/blog-data.ts`単独で1512箇所修正
- **取りこぼし要因**: `perl` one-linerはコードブロック内のサンプル文字列・HTML属性内・JSONエスケープ済み文字列まで一律に書き換えてしまい、Lintエラーや表示崩れを誘発した。文脈判定をskillに閉じ込めたのがこの動機

## Configuration

| Setting | Default | Description |
|---|---|---|
| Replacement | empty string | Removes the space; alternative: `--insert U+200B` for zero-width space |
| ASCII set | `[A-Za-z0-9_.\)\}\]>]` (left), `[A-Za-z0-9_\(\{\[<]` (right) | Punctuation chosen so `(日本語)` style boundaries are caught |
| CJK set | Hiragana + Katakana + CJK Unified + Halfwidth/Fullwidth Forms | See ranges above |
| Code block detection | Triple backtick + indented (4-space) | Markdown CommonMark |

## Reference files

- `references/cjk-ascii-boundary-rules.md` — Full Unicode range table, preserved-space rules, perl one-liner vs Python skill comparison
- `scripts/jp-ascii-space-fix.py` — Detector and rewriter

## Related skills

- `netsujo-aio:h1-mobile-check` — H1/H2 mobile line-break detector (sibling typography skill)
- `netsujo-aio:llms-txt-generator` — Generates llms.txt from source — relies on clean source strings
- `claude-seo:seo-content` — Content quality (E-E-A-T); pairs well with typography cleanup before publishing
