/* Optional actual browser regression. Requires existing Playwright/browser. MIT License. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

(async()=>{
  const browser = await chromium.launch({ headless:true });
  try {
    const page = await browser.newPage();
    await page.setContent('<html lang="ja"><style>p{font:20px sans-serif;width:100px;line-break:strict;word-break:normal;margin:0}.group{white-space:nowrap}</style><p id="bad">3つの事例を、ご覧ください。</p>');
    await page.addScriptTag({path:path.join(__dirname,'collect-rendered-lines.js')});
    let bad = await page.evaluate(()=>collectJapaneseLines('#bad',{protected:['3つの事例を、']}));
    assert.ok(bad.elements[0].lines.length>1);
    // Ensure a declared protected phrase actually crosses some rendered boundary.
    const span=bad.elements[0].protectedSpans[0];
    assert.ok(bad.elements[0].lines.some(l=>span.start<l.end && l.end<span.end));
    await page.setContent('<html lang="ja"><style>p{font:20px sans-serif;width:240px;line-break:strict;word-break:normal;margin:0}.group{white-space:nowrap}</style><p id="good"><span class="group">3つの事例を、</span>ご覧ください。</p>');
    await page.addScriptTag({path:path.join(__dirname,'collect-rendered-lines.js')});
    const good=await page.evaluate(()=>collectJapaneseLines('#good',{protected:['3つの事例を、']}));
    const g=good.elements[0], s=g.protectedSpans[0];
    assert.equal(g.overflow,false);
    assert.equal(g.unsupported.length,0);
    assert.ok(!g.lines.some(l=>s.start<l.end && l.end<s.end));
    await assert.rejects(()=>page.evaluate(()=>collectJapaneseLines('#missing')),/Matched/);
    console.log('Actual browser: split detected, scoped grouping intact, missing target rejected.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
