# Web layout and rendered evidence

## Scoped controls

Use declared language and normal wrapping for prose:

```html
<p lang="ja" class="ja-prose">...</p>
```

```css
.ja-prose {
  max-inline-size: 36em;
  word-break: normal;
  line-break: strict;
}
.ja-group { white-space: nowrap; }
```

Apply `.ja-group` only to **selected short spans that fit the minimum text-box width**:

```html
<p lang="ja" class="ja-prose">...<span class="ja-group">どの関わり方でも、</span>あなた自身の目的と意思を尊重します。</p>
```

Avoid indentation whitespace around inline spans if it changes visible copy. If the span does not fit, adjust layout, choose a smaller valid protected span, or use authorized shorter copy.

The example's `36em` is an editorial starting point, not a universal limit. Keep a wide card or section when its structure needs it, while constraining its prose independently. Preserve intentional left/center alignment and leave natural whitespace beside a narrower column. Do not expand text to consume available space. Use `em` or a measured `ic` policy for Japanese; `ch` measures a font's zero glyph and is not a CJK character count. Judge occupied line width as well as the box width: a short label in a wide box is not an overlong line.

Review the longest line and the rhythm of the paragraph. A 52em body line can be uncomfortable even when its break is legal. Start ordinary body review around 30–40em and short prominent lead copy around 24–36em, then verify and adjust for the design, density, font and audience. Do not enforce a minimum by widening mobile text. The collector's default review budgets are 40em for body and 36em for lead; supply an explicitly reviewed `maxLineEm` policy when a surface requires a different budget. These heuristics are not JLREQ requirements.

If the project permits it, short display headings can use soft boundaries with `wbr` and scoped `keep-all` when the selected segments fit. Honor project policies that prohibit `br`/`wbr`; use short inline groups instead:

```html
<h1 lang="ja" class="ja-display">Webサイトを、<wbr>営業基盤へ。</h1>
```

```css
.ja-display { word-break: keep-all; line-break: strict; }
```

Do not apply `keep-all` to all Japanese paragraphs. `line-break: strict` handles punctuation/small kana constraints, not semantic recognition. `text-wrap: balance`/`pretty` may improve line shape; neither proves semantic boundaries or browser consistency. Verify target support. Scope `overflow-wrap: anywhere` to exceptional long tokens: it may defeat grouping. Avoid `break-all` for normal Japanese/Latin copy.

## Browser collector

Use an existing authorized page/test harness; load the script through the browser tool's supported mechanism. With Playwright already in the project:

```js
await page.addScriptTag({ path: '/absolute/skill/path/scripts/collect-rendered-lines.js' });
const evidence = await page.evaluate(async () => await collectJapaneseLines(
  '.lead, .card-copy',
  { protected: ['どの関わり方でも、', '3つの事例を、'], minElements: 2 }
));
// Save evidence JSON using the project's filesystem API.
```

Repeat collection at each actual width; never resize old evidence. The collector waits for fonts and two animation frames, not application readiness. Check font requests: `fonts.ready` can resolve after failure. Deliberately test fallback fonts.

Optional attributes: `data-ja-surface="heading"` (or `label`, `body`, `lead`, `caption`); `data-ja-protect='["3つの事例を、"]'` augments global selected phrases. `data-ja-max-line-em="36"` declares a surface budget; the option `maxLineEm` provides a common override. Record why an override is readable, rather than increasing it to silence a finding.

Output schema: `{"schemaVersion":2,"viewport":{...},"elements":[...]}`. Each element has `text`, `lines` (`text`, `start`, `end`, `y`, `left`, `right`, `widthPx`), `measure` (`fontSizePx`, `maxLineEm`), `protectedSpans` (`text`, `start`, `end`), `overflow`, `unsupported`, `surface` and styles. Offsets are JavaScript UTF-16 indices. `widthPx / fontSizePx` is the occupied line measure in em, not a character count. Supply exact lines and measured geometry for document/OCR evidence; do not invent geometry or DOM provenance. Version 1 evidence lacks the mandatory measure and must be recollected.

Some browser tools expose only read-only DOM snapshots/styles and omit Range or TreeWalker APIs. A reported text-box width can support a width diagnosis, but cannot establish rendered line boundaries. Use supported screenshots and the project's authorized test runtime; do not invent line data, use forbidden browser APIs or mark the unsupported collector PASS.

```bash
python3 /absolute/skill/path/scripts/review-lines.py evidence.json
```

Exit `0`: no automated findings, still require screenshot and review of every semantic boundary. Exit `1`: acceptance blocked by a confirmed issue or unresolved editorial candidate, including a 1–2-character continuation line in body copy. Exit `2`: missing, invalid or unsupported evidence. Record contextual acceptance separately and tie it to the exact artifact/width; there is no blanket waiver flag. Confirmed particle/bunsetsu/name/compound/product/role/number-unit splits must be repaired. The linter does not infer complete Japanese grammar: explicitly review and declare the target's meaning units before treating the rendered result as verified.

## Limits

The collector uses grapheme Range rectangles for simple horizontal blocks. It rejects transforms, ruby, pseudo text, hidden descendants and multi-column layouts. Mixed font sizes/vertical alignment or complex boxes can yield multiple rows within one visual line: use screenshot review and an appropriate alternative. Range rectangles are not glyph ink bounds. Clipping, ellipsis, clamp, SVG, canvas, raster text and vertical writing need separate verification. No browser dependency is bundled.

## Specification basis

[CSS Text Level 3](https://www.w3.org/TR/css-text-3/#word-break-property) explains `word-break`/`wbr`; [JLREQ](https://www.w3.org/TR/jlreq/) covers Japanese line composition. Semantic grouping and tail thresholds are editorial policy, not standard conformance.
