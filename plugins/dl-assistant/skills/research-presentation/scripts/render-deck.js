#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { args, write } = require('./lib');
const { open, visit, overflow } = require('./browser');
async function render(html, out) {
  if (fs.existsSync(out) && fs.readdirSync(out).length) throw new Error('Use an empty output directory; existing renders are not overwritten');
  fs.mkdirSync(out, { recursive: true });
  const report = { html: path.resolve(html), live_states: [], export_slides: [], issues: [], passed: false };
  const live = await open(html);
  try {
    for (const slide of live.slides) {
      for (const fragment of [-1, ...new Set(slide.fragments)]) {
        await visit(live.page, slide, fragment);
        const file = `live-${String(slide.index).padStart(3, '0')}-f${fragment + 1}.png`;
        write(path.join(out, file), await live.page.screenshot());
        report.live_states.push({ id: slide.id, fragment, file, ...await overflow(live.page) });
      }
    }
    report.issues.push(...live.issues);
  } finally { await live.close(); }
  const preview = await open(html, true);
  try {
    for (const slide of preview.slides) {
      await visit(preview.page, slide);
      const file = `slide-${String(slide.index).padStart(3, '0')}.png`;
      write(path.join(out, file), await preview.page.screenshot());
      report.export_slides.push({ id: slide.id, file, ...await overflow(preview.page) });
    }
    const notes = await preview.page.evaluate(() => Reveal.getSlides().map(s => ({ id: s.id, title: s.querySelector('h1,h2')?.textContent || s.id, notes: s.querySelector('aside.notes')?.textContent || '' })));
    write(path.join(out, 'speaker-notes.md'), notes.map(n => `## ${n.title}\n\n${n.notes}\n`).join('\n'));
    report.issues.push(...preview.issues);
  } finally { await preview.close(); }
  const pdf = await open(html, true, true);
  try {
    await pdf.page.waitForFunction(() => window.presentationPdfReady === true, { timeout: 15000 });
    await pdf.page.evaluate(() => document.fonts.ready);
    const bytes = await pdf.page.pdf({ width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true });
    write(path.join(out, 'presentation.pdf'), bytes);
    report.issues.push(...pdf.issues);
  } finally { await pdf.close(); }
  report.passed = report.export_slides.length > 0 && !report.issues.length && ![...report.live_states, ...report.export_slides].some(s => s.hasOverflow);
  write(path.join(out, 'render-report.json'), JSON.stringify(report, null, 2));
  return report;
}
if (require.main === module) {
  (async () => {
    const o = args(process.argv.slice(2), ['html', 'out']);
    if (!o.html || !o.out) throw new Error('Usage: node render-deck.js --html talk.html --out new-render-directory');
    const r = await render(o.html, o.out); console.log(JSON.stringify({ passed: r.passed, slides: r.export_slides.length, live_states: r.live_states.length, issues: r.issues })); process.exitCode = r.passed ? 0 : 1;
  })().catch(e => { console.error(e.message); process.exitCode = 3; });
}
module.exports = { render };
