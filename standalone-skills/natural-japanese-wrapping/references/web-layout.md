# Web layout and rendered evidence

## Scoped controls

Use declared language and normal wrapping for prose:

```html
<p lang="ja" class="ja-prose">...</p>
```

```css
.ja-prose { word-break: normal; line-break: strict; }
.ja-group { white-space: nowrap; }
```

Apply `.ja-group` only to **selected short spans that fit the minimum text-box width**:

```html
<p lang="ja" class="ja-prose">...<span class="ja-group">どの関わり方でも、</span>あなた自身の目的と意思を尊重します。</p>
```

Avoid indentation whitespace around inline spans if it changes visible copy. If the span does not fit, adjust layout, choose a smaller valid protected span, or use authorized shorter copy.

For short display headings only, choose soft boundaries with `wbr` and scoped `keep-all`, if the selected segments fit:

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

Optional attributes: `data-ja-surface="heading"` (or `label`, `body`, `caption`); `data-ja-protect='["3つの事例を、"]'` augments global selected phrases.

Output schema: `{"schemaVersion":1,"viewport":{...},"elements":[...]}`. Each element has `text`, `lines` (`text`, `start`, `end`, `y`), `protectedSpans` (`text`, `start`, `end`), `overflow`, `unsupported`, `surface` and styles. Offsets are JavaScript UTF-16 indices. Supply exact line strings with this schema for manually collected document/OCR evidence; do not invent geometry or DOM provenance.

```bash
python3 /absolute/skill/path/scripts/review-lines.py evidence.json
```

Exit `0`: no automated findings, still require screenshot and semantic review. Exit `1`: confirmed issue or unresolved editorial candidate. Exit `2`: missing, invalid or unsupported evidence. Record contextual acceptance separately and tie it to the exact artifact/width; there is no blanket waiver flag.

## Limits

The collector uses grapheme Range rectangles for simple horizontal blocks. It rejects transforms, ruby, pseudo text, hidden descendants and multi-column layouts. Mixed font sizes/vertical alignment or complex boxes can yield multiple rows within one visual line: use screenshot review and an appropriate alternative. Range rectangles are not glyph ink bounds. Clipping, ellipsis, clamp, SVG, canvas, raster text and vertical writing need separate verification. No browser dependency is bundled.

## Specification basis

[CSS Text Level 3](https://www.w3.org/TR/css-text-3/#word-break-property) explains `word-break`/`wbr`; [JLREQ](https://www.w3.org/TR/jlreq/) covers Japanese line composition. Semantic grouping and tail thresholds are editorial policy, not standard conformance.
