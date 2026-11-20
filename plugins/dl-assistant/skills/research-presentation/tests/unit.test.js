'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { contrast, readable } = require('../scripts/generate-theme');
const { chartConfig } = require('../assets/runtime');
const { check: charts, validateChart } = require('../scripts/check-charts');
const { check: content } = require('../scripts/check-content');
const { digest } = require('../scripts/lib');
const scripts = path.resolve(__dirname, '../scripts');
function temporary(t) { const root = fs.mkdtempSync(path.join(os.tmpdir(), 'slides-unit-')); t.after(() => fs.rmSync(root, { recursive: true, force: true })); return root; }
function cli(name, argv) { return spawnSync(process.execPath, [path.join(scripts, name), ...argv], { encoding: 'utf8' }); }
function plan() { return { schema_version: 1, title: '检查', scenario: 'group_meeting', audience: '研究者', goal: '讨论问题', talk_minutes: 1, sources: [], assets: [], slides: [{ id: 'question', title: '问题', question: '需要回答什么？', message: '目前未知', seconds: 30, evidence_ids: [], notes: '说明未知与需要的决定', visual: { kind: 'text', purpose: '提出明确讨论问题', text_only_reason: '简短问题页，不需要装饰图片' } }] }; }
const html = '<div class="reveal"><div class="slides"><section id="question"><h2>问题</h2><p>需要什么观察？</p></section></div></div>';

test('generator rejects malformed integers, missing values and unknown flags without overwriting', t => {
  const root = temporary(t), file = path.join(root, 'talk.html'); fs.writeFileSync(file, 'USER_CONTENT');
  for (const argv of [['--slides', '2abc'], ['--slides'], ['--unknown', 'x'], ['--structure', '1,,2']]) {
    const r = cli('create-presentation.js', [...argv, '--output', file]); assert.notEqual(r.status, 0); assert.equal(fs.readFileSync(file, 'utf8'), 'USER_CONTENT');
  }
});
test('new scaffold is escaped, local and explicitly incomplete; force preserves old source', t => {
  const root = temporary(t), file = path.join(root, 'talk.html');
  let r = cli('create-presentation.js', ['--slides', '2', '--title', '<script>unsafe</script>', '--output', file]); assert.equal(r.status, 0, r.stderr);
  const source = fs.readFileSync(file, 'utf8'); assert.ok(source.includes('&lt;script&gt;')); assert.ok(source.includes('data-placeholder')); assert.ok(!source.includes('https://'));
  r = cli('create-presentation.js', ['--slides', '3', '--output', file]); assert.notEqual(r.status, 0); assert.equal(fs.readFileSync(file, 'utf8'), source);
  r = cli('create-presentation.js', ['--slides', '3', '--output', file, '--force']); assert.equal(r.status, 0, r.stderr);
  const backup = fs.readdirSync(root).find(n => n.startsWith('talk.html.bak-')); assert.equal(fs.readFileSync(path.join(root, backup), 'utf8'), source);
});
test('generator rejects stylesheet escape and unsupported features before writing', t => {
  const root = temporary(t), file = path.join(root, 'talk.html');
  for (const argv of [['--styles', '../outside.css'], ['--features', 'unknown']]) assert.notEqual(cli('create-presentation.js', [...argv, '--output', file]).status, 0);
  assert.ok(!fs.existsSync(file));
});
test('theme adjusts unreadable primary colors and rejects invalid options', t => {
  assert.ok(contrast(readable('#fff', '#fff'), '#fff') >= 4.5);
  assert.ok(contrast(readable('#000', '#17232f'), '#17232f') >= 4.5);
  const root = temporary(t), file = path.join(root, 'theme.css');
  for (const argv of [['--primary', 'invalid'], ['--mode', 'unknown'], ['--font-pairing', 'unknown']]) assert.notEqual(cli('generate-theme.js', [...argv, '--output', file]).status, 0);
  assert.ok(!fs.existsSync(file));
  assert.equal(cli('generate-theme.js', ['--primary', '#fff', '--output', file]).status, 0);
  assert.notEqual(cli('generate-theme.js', ['--output', file]).status, 0);
});
test('CSV supports quoted commas, escaped quotes, nulls and rejects malformed rows', () => {
  const r = chartConfig('label,value\n"a,b",1\n"a""b",\n'); assert.deepEqual(r.data.labels, ['a,b', 'a"b']); assert.deepEqual(r.data.datasets[0].data, [1, null]);
  for (const x of ['label,value\nx,NaN', 'label,value\nx,1,2', 'label,value\n"x,1']) assert.throws(() => chartConfig(x));
});
test('chart validation rejects empty, nonfinite, mismatched and invalid scatter data', () => {
  for (const [c, type] of [[{}, 'bar'], [{ data: { labels: ['a'], datasets: [{ data: [1, 2] }] } }, 'line'], [{ data: { datasets: [{ data: [Infinity] }] } }, 'bar'], [{ data: { datasets: [{ data: [{ x: 1 }] }] } }, 'scatter']]) assert.ok(validateChart(c, type).length);
  assert.deepEqual(validateChart({ data: { datasets: [{ data: [{ x: 1, y: 2 }] }] } }, 'scatter'), []);
});
test('external chart source is actually checked and cannot escape deck directory', t => {
  const root = temporary(t), file = path.join(root, 'talk.html');
  fs.writeFileSync(file, '<canvas data-chart="bar" data-chart-src="missing.json"></canvas>'); assert.equal(charts(file).passed, false);
  fs.writeFileSync(file, '<canvas data-chart="bar" data-chart-src="https://example.invalid/data.json"></canvas>'); assert.equal(charts(file).passed, false);
  fs.writeFileSync(file, '<canvas data-chart="bar"><!--{"data":{"labels":["a"],"datasets":[{"data":[1]}]}}--></canvas>'); assert.equal(charts(file).passed, true);
});
test('purposeful text slide is allowed; visual decision cannot be omitted', t => {
  const root = temporary(t), p = plan(); assert.equal(content(p, html, root).passed, true);
  delete p.slides[0].visual.text_only_reason; assert.equal(content(p, html, root).passed, false);
  delete p.slides[0].visual; assert.equal(content(p, html, root).passed, false);
});
test('planning an image is not completion; ready asset must exist and be placed', t => {
  const root = temporary(t), p = plan();
  p.assets = [{ id: 'diagram', purpose: '说明关系', alt: '流程图', file: 'diagram.svg', source: { kind: 'schematic', ref: '根据研究记录绘制' }, label: '示意', status: 'planned' }];
  p.slides[0].visual = { kind: 'diagram', purpose: '说明关系', asset_ids: ['diagram'] };
  assert.ok(content(p, html, root).incomplete.length);
  p.assets[0].status = 'ready'; assert.ok(content(p, html, root).errors.length);
  fs.writeFileSync(path.join(root, 'diagram.svg'), '<svg xmlns="http://www.w3.org/2000/svg"></svg>');
  assert.ok(content(p, html, root).incomplete.length);
  assert.ok(content(p, html.replace('<p>', '<p data-asset-id="diagram">'), root).incomplete.length);
  const placed = html.replace('<p>', '<img src="diagram.svg" alt="流程图" data-asset-id="diagram"><p>');
  assert.equal(content(p, placed, root).passed, true);
  p.assets[0].sha256 = digest('different'); assert.equal(content(p, placed, root).passed, false);
});
test('interactive/media slides need static replacement and unplanned slides fail', t => {
  const root = temporary(t), p = plan();
  const interactive = html.replace('<p>', '<div data-interactive></div><p>'); assert.equal(content(p, interactive, root).passed, false);
  const extra = html.replace('</section>', '</section><section id="unplanned"></section>'); assert.equal(content(p, extra, root).passed, false);
});
test('main talk budget is enforced while appendix is separate', t => {
  const root = temporary(t), p = plan(); p.slides[0].seconds = 90; assert.equal(content(p, html, root).passed, false);
  p.slides[0].role = 'appendix'; assert.equal(content(p, html, root).passed, true);
});
