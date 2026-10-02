# Verification cases

Validate on fresh artifacts without supplying expected fixes. Include headings, prose and fixed canvases.

1. A lead paragraph with a particle starting its second line; preserve approved wording at several widths.
2. A mobile heading with a company name and price; preserve both without overflow.
3. A long article with ordinary word-internal wrapping; avoid unnecessary grouping and whitespace.
4. An independent word beginning with `も`, such as `もっと`; avoid a false grammatical rejection.
5. Explicit breaks and soft wrapping; distinguish source inspection from screenshot-only inference.
6. A protected phrase wider than the box; reject blanket nowrap as a sufficient fix.
7. A missing selector or unsupported ruby/vertical/clamped element; report missing evidence, not PASS.
8. A fixed-canvas caption or PDF with an inflected verb tail; inspect exported output.
9. A desktop body paragraph with legal breaks and a very wide occupied line; improve readability while preserving copy and responsive fit.
10. A short label inside a wide container; distinguish occupied line width from box width and avoid a false overlong-line rejection.
11. A mixed Japanese/Latin paragraph; use measured line width rather than character count or `ch` as a Japanese proxy.
12. A whole-site completion request with only two inspected paragraphs; retain missing coverage and the production-bound release gate.

Run `python3 scripts/test-review-lines.py` and `node scripts/test-collector.cjs` for script regression. The second uses synthetic Range geometry and is **not** a real browser/font/layout test. If an actual browser and Playwright are available, run `node scripts/test-browser.cjs` as well. Record synthetic and actual-render results separately. Passing tests never proves naturalness for every sentence.
