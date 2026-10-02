---
name: natural-japanese-wrapping
description: Prevent and repair unnatural Japanese line breaks in prose, websites, UI labels, headings, slides, PDFs, captions and image text. Use when writing or laying out Japanese, reviewing typography, fixing orphaned particles or split phrases, or handling complaints about 改行, 折り返し, 助詞の孤立 or 不自然な改行. Plan meaningful boundaries before generation and inspect actual rendered lines after layout.
---

# Natural Japanese Wrapping

Treat wrapping as part of reading comprehension. Optimize meaning, legibility and responsive fit together. Do not equate a technically allowed Japanese break with a good editorial break. Do not promise changed model weights or perfect output from installing a skill.

## 1. Establish the target before writing

- Identify the surface: prose, display heading, label, caption, fixed canvas or document.
- Record the approved copy, language, font, size, available **text-box** width and relevant widths/pages. Preserve approved copy; use existing authorization or obtain it before changing claims, numbers or wording.
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

Fix layout in this order: remove accidental hard breaks/inappropriate inherited CSS → select local semantic groups → improve text-box width/spacing → revise authorized copy if necessary. Change type size only within design/accessibility requirements. Never repair one width by causing overflow or unreadable text elsewhere.

## 4. Inspect the output, not just the source

For web work, use existing browser verification tools. Default to 320, 375, 768, 1024 and 1440 CSS px viewport widths if no supported range is given; also inspect actual component widths and both sides of breakpoints and observed wrap transitions. Check supported engines, fallback-font behavior and 200% text/zoom where feasible. Mark untested combinations explicitly.

Wait for fonts and application readiness. Collect **rendered** lines. Optionally load `scripts/collect-rendered-lines.js` in a browser, call `await collectJapaneseLines(selector, options)`, save JSON and run:

```bash
python3 scripts/review-lines.py rendered-lines.json
```

Pass selected exact phrases as `protected`, e.g. `["3つの事例を、"]`. Set `minElements` when the expected target count is known. Missing targets are errors, not passes. The collector supports simple horizontal, untransformed DOM text without ruby/pseudo text. Use screenshots/layout-specific tools for unsupported layouts. See the web reference for invocation and schema.

At **every** line boundary, read the line end and next line start as one phrase. Review particle/predicate isolation, names/units, punctuation, tiny display-copy tails, excess gaps, unintended hard breaks and reading order. Compare against full copy. Inspect screenshots too: geometry heuristics are incomplete. For prose without controllable rendering, verify authored breaks and mark visual wrapping untested.

## 5. Enforce the finish gate

Do not call typography verified while any condition remains:

1. A selected protected span crosses a rendered line, or content overflows/is clipped.
2. An editorial candidate is unresolved: repair it or record a specific contextual acceptance.
3. Required render evidence is absent, a selector matches nothing, or collection is unsupported.

Iterate and re-render changed targets and affected widths. Zero lint warnings do **not** establish semantic or visual PASS. A skill alone cannot enforce a pipeline: when requested, wire the collector, exit code and reviewed evidence into the project's completion/CI workflow. Do not claim cross-agent rollout from installation in one environment.

Report briefly: offending boundary, fix, tested widths/fonts/surface, remaining limitation. Keep reasoning internal unless asked. Read [references/verification-cases.md](references/verification-cases.md) when validating this skill; use fresh tasks rather than only the examples above.
