#!/usr/bin/env node
'use strict';
const { args, write } = require('./lib');
const { open, visit, overflow } = require('./browser');
async function check(html) {
  const app = await open(html);
  try {
    const results = [];
    for (const slide of app.slides) {
      for (const fragment of [-1, ...new Set(slide.fragments)]) {
        await visit(app.page, slide, fragment);
        results.push({ slide: slide.index, id: slide.id, fragment, ...await overflow(app.page) });
      }
    }
    return { checked_states: results.length, results, issues: app.issues, passed: results.length > 0 && !results.some(s => s.hasOverflow) && app.issues.length === 0 };
  } finally { await app.close(); }
}
async function main() {
  const positional = process.argv[2];
  if (!positional || positional.startsWith('--')) throw new Error('Usage: node check-overflow.js talk.html [--report result.json]');
  const o = args(process.argv.slice(3), ['report'], ['force']);
  const result = await check(positional);
  if (o.report) write(o.report, JSON.stringify(result, null, 2), o.force);
  console.log(JSON.stringify(result));
  return result.passed ? 0 : 1;
}
if (require.main === module) main().then(code => { process.exitCode = code; }).catch(e => { console.error(e.message); process.exitCode = 3; });
module.exports = { check };
