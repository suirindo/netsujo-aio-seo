/* MIT License. Run inside an authorized browser page. Horizontal DOM text only. */
(function (scope) {
  'use strict';
  scope.collectJapaneseLines = async function (selector, options = {}) {
    if (typeof selector !== 'string' || !selector.trim()) throw new Error('A target selector is required.');
    if (document.fonts) await document.fonts.ready;
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const targets = [...document.querySelectorAll(selector)];
    const minimum = options.minElements ?? 1;
    if (!Number.isInteger(minimum) || minimum < 1) throw new Error('minElements must be a positive integer.');
    if (targets.length < minimum) throw new Error(`Matched ${targets.length} targets; expected at least ${minimum}.`);
    if (targets.some(a => targets.some(b => a !== b && a.contains(b)))) throw new Error('Select non-overlapping text blocks.');
    if (options.protected && (!Array.isArray(options.protected) || options.protected.some(x => typeof x !== 'string' || !x))) throw new Error('protected must contain nonempty strings.');
    const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter('ja', { granularity: 'grapheme' }) : null;
    const elements = targets.map((el, index) => {
      const style = getComputedStyle(el), box = el.getBoundingClientRect();
      const unsupported = new Set();
      if (!segmenter) unsupported.add('Intl.Segmenter unavailable');
      if (style.writingMode !== 'horizontal-tb') unsupported.add('non-horizontal writing');
      if (style.columnCount !== 'auto' && Number(style.columnCount) > 1) unsupported.add('multiple columns');
      if (style.columnWidth !== 'auto') unsupported.add('column width');
      if (style.webkitLineClamp && !['none', '0'].includes(style.webkitLineClamp)) unsupported.add('line clamp');
      if (style.textOverflow === 'ellipsis') unsupported.add('ellipsis');
      if (el.querySelector('ruby, rt, svg, canvas, input, textarea')) unsupported.add('non-simple text content');
      for (let ancestor = el; ancestor; ancestor = ancestor.parentElement) {
        const s = getComputedStyle(ancestor);
        if (s.transform !== 'none' || (s.rotate && s.rotate !== 'none') || (s.scale && s.scale !== 'none')) unsupported.add('transformed geometry');
      }
      const children = [el, ...el.querySelectorAll('*')];
      for (const child of children) {
        const s = getComputedStyle(child);
        if (s.display === 'none' || s.visibility !== 'visible' || Number(s.opacity) === 0) unsupported.add('hidden content');
        if (s.fontSize !== style.fontSize || !['baseline', 'normal'].includes(s.verticalAlign)) unsupported.add('mixed vertical metrics');
        for (const pseudo of ['::before', '::after']) {
          const content = getComputedStyle(child, pseudo).content;
          if (content && !['none', 'normal', '""', "''"].includes(content)) unsupported.add('pseudo-element content');
        }
      }
      let phrases = options.protected ? [...options.protected] : [];
      if (el.dataset.jaProtect) {
        try {
          const local = JSON.parse(el.dataset.jaProtect);
          if (!Array.isArray(local) || local.some(x => typeof x !== 'string' || !x)) throw new Error();
          phrases.push(...local);
        } catch (_) { unsupported.add('invalid data-ja-protect'); }
      }
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let node, text = '', lines = [], pending = '', overflow = false;
      const range = document.createRange();
      while ((node = walker.nextNode())) {
        const base = text.length; text += node.data;
        const segments = segmenter ? [...segmenter.segment(node.data)] : [];
        for (const part of segments) {
          range.setStart(node, part.index); range.setEnd(node, part.index + part.segment.length);
          const rects = [...range.getClientRects()].filter(r => r.width > 0.01 && r.height > 0.01);
          if (rects.length !== 1) {
            if (!/^\s+$/u.test(part.segment)) unsupported.add('unmeasurable or fragmented grapheme');
            if (lines.length) { lines.at(-1).text += part.segment; lines.at(-1).end = base + part.index + part.segment.length; }
            else pending += part.segment;
            continue;
          }
          const r = rects[0], offset = base + part.index;
          if (r.right > box.right + 1 || r.left < box.left - 1 || r.bottom > box.bottom + 1 || r.top < box.top - 1) overflow = true;
          const previous = lines.at(-1);
          if (previous && Math.abs(previous.y - r.top) < 2) {
            previous.text += part.segment; previous.end = offset + part.segment.length;
          } else {
            lines.push({ text: pending + part.segment, start: offset - pending.length, end: offset + part.segment.length, y: r.top });
            pending = '';
          }
        }
      }
      if (!text.trim() || !lines.length) unsupported.add('empty or unmeasurable target');
      if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) overflow = true;
      const protectedSpans = [];
      for (const phrase of new Set(phrases)) {
        let start = text.indexOf(phrase);
        while (start >= 0) {
          protectedSpans.push({ text: phrase, start, end: start + phrase.length });
          start = text.indexOf(phrase, start + 1);
        }
      }
      const missingProtected = el.dataset.jaProtect ? phrases.filter(p => !text.includes(p) && !options.protected?.includes(p)) : [];
      if (missingProtected.length) unsupported.add('declared local protected phrase missing');
      return { target: el.id ? `#${el.id}` : `${selector}[${index}]`, surface: el.dataset.jaSurface || (/^H[1-6]$/.test(el.tagName) ? 'heading' : 'body'), text, lines, protectedSpans, overflow, unsupported: [...unsupported], styles: { font: style.font, wordBreak: style.wordBreak, lineBreak: style.lineBreak, whiteSpace: style.whiteSpace }, box: { width: box.width, height: box.height } };
    });
    return { schemaVersion: 1, viewport: { width: innerWidth, height: innerHeight, dpr: devicePixelRatio }, elements };
  };
})(globalThis);
