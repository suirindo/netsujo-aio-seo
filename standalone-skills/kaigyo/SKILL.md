---
name: kaigyo
description: Make Japanese text comfortable to read by controlling paragraph structure, line length, semantic boundaries and responsive wrapping. Use when writing or laying out Japanese in prose, websites, UI, slides, PDFs, captions or images, reviewing typography, or handling complaints about 改行, 折り返し, 不自然な改行, 一文が横に長い, 読みにくい or 助詞の孤立. Inspect rendered line widths and boundaries together.
---

# kaigyo

Treat wrapping as part of reading comprehension. Optimize meaning, readable line length, line shape and responsive fit together. A phrase that stays intact across a very wide line can still be difficult to read. Do not equate legal Japanese breaks, zero overflow or zero lint findings with good typography. Do not promise changed model weights or perfect output from installing a skill.

Use the Netsujo implementation of `kaigyo`; identify it by its publisher and source when distributing it. The name is also used by an independent Japanese-wrapping skill. Do not claim global name uniqueness or affiliation with that implementation.

## 1. Establish the target before writing

- Identify the surface: prose, display heading, label, caption, fixed canvas or document.
- Record the approved copy, language, font, size, available **text-box** width and relevant widths/pages. Preserve approved copy; use existing authorization or obtain it before changing claims, numbers or wording.
- Set a readable line-length budget for each surface before layout. For ordinary Japanese web body copy, start with a column around 30–40 em; use a narrower starting point for prominent short introductions. These are adjustable editorial starting points, not standards or automatic approval. Measure actual lines at the actual font. `40ch` does not mean 40 Japanese characters.
- Distinguish paragraph boundaries, intentional hard breaks and automatic visual wrapping. A screenshot alone cannot identify the source; inspect markup/computed styles when available. Never invent a `<br>` diagnosis from pixels.
- For chat/Markdown prose, write connected paragraphs. Do not insert newlines inside a sentence to imitate screen width. Preserve structural newlines in lists, tables, code, addresses, lyrics and user-requested formats.

## 2. Plan meaningful boundaries before layout

Read the complete sentence, then select short spans whose separation harms this particular surface. Keep the list small and explicit: a prominent noun with its short particle, an inflected predicate, a proper name, a number with its unit. Prefer clause/sentence boundaries when they improve short display copy.

| Boundary | Default judgment |
| --- | --- |
| `どの関わり方で｜も、` / `3つの事例｜を、` | Repair prominent copy: a particle is detached from its phrase. |
| `申し込みできま｜す。` | Repair the conspicuous tiny predicate tail. |
| `月額7｜万円` / `Netsu｜jo SIGNAL` | Protect the approved value/unit or name if it fits. |
| `Webサイトを、｜営業基盤へ。` | Accept an intentional heading boundary if fitting and balanced. |
| A body sentence stretched across the page with a large eye movement to its next line | Repair the text column even if every break is grammatically acceptable. |
| A long body paragraph breaking inside a Japanese word | Evaluate in context; do not prohibit ordinary Japanese character wrapping. |

Do **not** ban every line beginning with `の`, `に`, `を`, `は` or `も`: some are independent words or acceptable prose. Apply grammatical context, prominence and line shape. Treat automated particle matches as review candidates, not linguistic proof. Apply punctuation constraints separately from these editorial choices.

Read [references/japanese-review.md](references/japanese-review.md) for Japanese examples. Read [references/web-layout.md](references/web-layout.md) before web changes.

## 3. Generate for the surface

- Prose: use normal Japanese wrapping; protect only selected important spans when warranted.
- Short headings: define preferred semantic groups and soft opportunities; use a hard break only for a clear editorial purpose that fits all required layouts.
- Labels: preserve meaning and readable size; increase space or revise authorized copy before clipping it.
- Slides/PDFs/captions: measure at the actual font and canvas; never break at a constant character count. Inspect exported pages/frames. Match subtitle boundaries to timing and spoken phrases.
- Images: use separate controllable typography when exact wording and breaks matter; inspect final images. A generation prompt cannot guarantee glyphs or line boundaries.
- Preserve selectable/searchable text and accessible reading order where supported. Do not add visible spaces or invisible characters to canonical copy solely for layout.

Fix layout in this order: remove accidental hard breaks/inappropriate inherited CSS → choose a readable text column and alignment → protect selected short semantic groups → tune spacing/line shape → revise authorized copy if necessary. Limit prose width independently of a wider card or section. Do not add a fixed newline every N characters, force every sentence onto its own line, fill a wide container with text, or shrink the type to keep a sentence on one line. Re-read all boundaries after changing width: a narrower column can expose new splits. Never repair one width by causing overflow, excessive raggedness or unreadable text elsewhere.

## 4. Inspect the output, not just the source

For web work, use existing browser verification tools. Default to 320, 375, 768, 1024 and 1440 CSS px viewport widths if no supported range is given; also inspect actual component widths and both sides of breakpoints and observed wrap transitions. Check supported engines, fallback-font behavior and 200% text/zoom where feasible. Mark untested combinations explicitly.

Wait for fonts and application readiness. Collect **rendered** lines. Optionally load `scripts/collect-rendered-lines.js` in a browser, call `await collectJapaneseLines(selector, options)`, save JSON and run:

```bash
python3 scripts/review-lines.py rendered-lines.json
```

Pass selected exact phrases as `protected`, e.g. `["3つの事例を、"]`. Set `minElements` when the expected target count is known. Missing targets are errors, not passes. The collector supports simple horizontal, untransformed DOM text without ruby/pseudo text. Use screenshots/layout-specific tools for unsupported layouts. See the web reference for invocation and schema.

Check **both** line width and boundaries. At every boundary, read the line end and next line start as one phrase. Review particle/predicate isolation, names/units, punctuation, tiny display-copy tails, excess gaps, unintended hard breaks and reading order. Assess the longest occupied line, the return to the next line, paragraph density and alignment; do not use an average that hides one overlong line. Compare against full copy. Inspect screenshots too: geometry heuristics are incomplete. For prose without controllable rendering, verify authored breaks and paragraph structure and mark visual wrapping/line measure untested.

## 5. Enforce the finish gate

Do not call typography verified while any condition remains:

1. A selected protected span crosses a rendered line, or content overflows/is clipped.
2. A line exceeds the declared readable measure, or an editorial candidate is unresolved: repair it or record a specific contextual acceptance tied to the surface and rendered width.
3. Required render evidence is absent, a selector matches nothing, or collection is unsupported.

Iterate and re-render changed targets and affected widths. Zero lint warnings do **not** establish semantic or visual PASS. A skill alone cannot enforce a pipeline: when requested, wire the collector, exit code and reviewed evidence into the project's completion/CI workflow. Do not claim cross-agent rollout from installation in one environment.

For a whole public site, inventory public URLs, shared templates and visible UI states; bind the review to the deployed version. Cover required widths and fonts, record every finding and contextual acceptance, and recheck changed pages and shared consumers after deployment. Checking two paragraphs does not establish site-wide completion. Keep untested pages or combinations explicit. If formal publication depends on the public-site repair, keep the release in review until that production evidence is complete; draft code or preview checks cannot satisfy it.

Report briefly: offending boundary, fix, tested widths/fonts/surface, remaining limitation. Keep reasoning internal unless asked. Read [references/verification-cases.md](references/verification-cases.md) when validating this skill; use fresh tasks rather than only the examples above.
