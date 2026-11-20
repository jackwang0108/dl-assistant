'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { open, visit } = require('../scripts/browser');
const { check: overflow } = require('../scripts/check-overflow');
const { render } = require('../scripts/render-deck');
const { demo } = require('../scripts/create-demo');
const { check: content } = require('../scripts/check-content');
const chrome = [process.env.PUPPETEER_EXECUTABLE_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome'].filter(Boolean).some(p => fs.existsSync(p));
function directory(t) { const root = fs.mkdtempSync(path.join(os.tmpdir(), 'slides-browser-')); t.after(() => fs.rmSync(root, { recursive: true, force: true })); return root; }
function scaffold(root) {
  const file = path.join(root, 'talk.html');
  const r = spawnSync(process.execPath, [path.join(__dirname, '../scripts/create-presentation.js'), '--slides', '2', '--output', file], { encoding: 'utf8' }); assert.equal(r.status, 0, r.stderr); return file;
}
test('hidden later page overflow is visited and makes CLI fail', { skip: !chrome }, async t => {
  const root = directory(t), file = scaffold(root); let text = fs.readFileSync(file, 'utf8');
  text = text.replace('<section id="slide-2">', '<section id="slide-2"><div style="position:absolute;width:1800px;height:100px;left:0;top:100px">known overflow</div>'); fs.writeFileSync(file, text);
  const result = await overflow(file); assert.equal(result.passed, false); assert.ok(result.results.some(r => r.id === 'slide-2' && r.hasOverflow));
  const r = spawnSync(process.execPath, [path.join(__dirname, '../scripts/check-overflow.js'), file], { encoding: 'utf8', timeout: 45000 }); assert.equal(r.status, 1, r.stderr);
});
test('runtime reports broken image and blocked external resources', { skip: !chrome }, async t => {
  const root = directory(t), file = scaffold(root); let source = fs.readFileSync(file, 'utf8');
  source = source.replace('<section id="slide-2">', '<section id="slide-2"><img src="missing.png" alt="missing">').replace('</head>', '<script src="https://example.invalid/external.js"></script></head>'); fs.writeFileSync(file, source);
  const result = await overflow(file); assert.equal(result.passed, false); assert.ok(result.issues.some(i => i.kind === 'external_resource')); assert.ok(result.issues.some(i => i.kind === 'render' || i.kind === 'http'));
});
test('invalid formula is a render failure rather than silently printed source', { skip: !chrome }, async t => {
  const root = directory(t), file = path.join(root, 'math.html');
  const created = spawnSync(process.execPath, [path.join(__dirname, '../scripts/create-presentation.js'), '--slides', '1', '--features', 'math', '--output', file], { encoding: 'utf8' });
  assert.equal(created.status, 0, created.stderr);
  fs.writeFileSync(file, fs.readFileSync(file, 'utf8').replace('<h2>', '<p>$$\\notARealKaTeXCommand{x}$$</p><h2>'));
  const result = await overflow(file); assert.equal(result.passed, false); assert.ok(result.issues.some(i => i.kind === 'render'));
});
test('real demo slider resets, media is local and hidden Mermaid has a useful viewBox', { skip: !chrome }, async t => {
  const root = directory(t); const built = demo(path.join(root, 'demo')); const app = await open(built.html);
  try {
    await visit(app.page, app.slides.find(s => s.id === 'threshold'));
    const output = () => app.page.$eval('#threshold-output', e => e.textContent);
    assert.ok((await output()).includes('2 / 4'));
    await app.page.$eval('#threshold-control', e => { e.value = '0.8'; e.dispatchEvent(new Event('input')); }); assert.ok((await output()).includes('1 / 4'));
    await app.page.click('#reset-threshold'); assert.ok((await output()).includes('2 / 4'));
    await visit(app.page, app.slides.find(s => s.id === 'audio'));
    await app.page.waitForFunction(() => document.getElementById('demo-audio').duration > 0);
    const duration = await app.page.$eval('#demo-audio', e => e.duration); assert.ok(Math.abs(duration - 1) < 0.01);
    await app.page.$eval('#demo-audio', e => { e.currentTime = 0.5; });
    await app.page.waitForFunction(() => Number(document.getElementById('playhead').getAttribute('x1')) > 300);
    await visit(app.page, app.slides.find(s => s.id === 'appendix'));
    const view = await app.page.$eval('.mermaid svg', e => e.getAttribute('viewBox').split(/\s+/).map(Number)); assert.ok(view[2] > 100, String(view));
    assert.ok(await app.page.$('.katex')); assert.ok(await app.page.$('canvas[data-chart]')); assert.deepEqual(app.issues, []);
  } finally { await app.close(); }
});
test('complete demo plan and actual browser/PDF export succeed with static replacements', { skip: !chrome }, async t => {
  const root = directory(t); const built = demo(path.join(root, 'demo'));
  const p = JSON.parse(fs.readFileSync(built.plan)); assert.equal(content(p, fs.readFileSync(built.html, 'utf8'), path.dirname(built.html)).passed, true);
  const result = await render(built.html, path.join(root, 'render'));
  assert.equal(result.passed, true, JSON.stringify(result)); assert.equal(result.export_slides.length, 8); assert.ok(result.live_states.length > 8);
  const pdf = fs.readFileSync(path.join(root, 'render/presentation.pdf')); assert.equal(pdf.subarray(0, 4).toString(), '%PDF');
  const app = await open(built.html, true);
  try {
    await visit(app.page, app.slides.find(s => s.id === 'threshold'));
    assert.equal(await app.page.$eval('#threshold-control', e => getComputedStyle(e.closest('[data-interactive]')).display), 'none');
    assert.notEqual(await app.page.$eval('#threshold-static', e => getComputedStyle(e).display), 'none');
  } finally { await app.close(); }
});
