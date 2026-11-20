'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createEditor } = require('../scripts/edit-html');
const { digest } = require('../scripts/lib');
async function setup(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'slides-editor-')); const dir = path.join(root, 'deck'); fs.mkdirSync(dir);
  const file = path.join(dir, 'talk.html'); const source = '<!doctype html><html><body><h2>原始标题</h2><p>正文</p><svg><text>保留SVG</text></svg><script>const originalData=[1,2,3];</script></body></html>'; fs.writeFileSync(file, source);
  const app = await createEditor(file); t.after(async () => { await new Promise(resolve => app.server.close(resolve)); fs.rmSync(root, { recursive: true, force: true }); });
  const html = await (await fetch(app.origin)).text(); const token = html.match(/'X-Edit-Token':"([a-f0-9]+)"/)[1];
  const save = (body, authorized = true) => fetch(app.origin + '/save', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(authorized ? { Origin: app.origin, 'X-Edit-Token': token } : {}) }, body: typeof body === 'string' ? body : JSON.stringify(body) });
  return { root, dir, file, source, app, save };
}
test('editor saves only requested source text, preserves scripts/SVG and creates backup', async t => {
  const x = await setup(t); const r = await x.save({ baseHash: digest(x.source), patches: [{ id: 'text-0', text: '<新标题>' }] }); assert.equal(r.status, 200);
  const result = fs.readFileSync(x.file, 'utf8'); assert.ok(result.includes('&lt;新标题&gt;')); assert.ok(result.includes('<svg><text>保留SVG</text></svg>')); assert.ok(result.includes('<script>const originalData=[1,2,3];</script>'));
  const backup = fs.readdirSync(x.dir).find(n => n.includes('.bak-')); assert.equal(fs.readFileSync(path.join(x.dir, backup), 'utf8'), x.source);
});
test('editor rejects stale save after external edit without overwriting it', async t => {
  const x = await setup(t); fs.writeFileSync(x.file, x.source + '<!-- external change -->');
  assert.equal((await x.save({ baseHash: digest(x.source), patches: [{ id: 'text-0', text: 'overwrite' }] })).status, 409);
  assert.ok(fs.readFileSync(x.file, 'utf8').endsWith('<!-- external change -->'));
});
test('editor rejects unauthorized, malformed and oversized writes', async t => {
  const x = await setup(t); assert.equal((await x.save({}, false)).status, 403); assert.equal((await x.save('{')).status, 400);
  assert.equal((await x.save('x'.repeat(2 * 1024 * 1024 + 1))).status, 413); assert.equal(fs.readFileSync(x.file, 'utf8'), x.source);
});
test('static serving rejects path and symlink escapes', async t => {
  const x = await setup(t); fs.writeFileSync(path.join(x.root, 'secret.txt'), 'outside'); fs.symlinkSync(path.join(x.root, 'secret.txt'), path.join(x.dir, 'leak.txt'));
  for (const route of ['/..%2fsecret.txt', '/leak.txt']) { const r = await fetch(x.app.origin + route); assert.equal(r.status, 404); assert.ok(!(await r.text()).includes('outside')); }
});
test('local media server supports byte ranges and rejects invalid ranges', async t => {
  const x = await setup(t); fs.writeFileSync(path.join(x.dir, 'media.dat'), '0123456789');
  let r = await fetch(x.app.origin + '/media.dat', { headers: { Range: 'bytes=2-5' } });
  assert.equal(r.status, 206); assert.equal(r.headers.get('content-range'), 'bytes 2-5/10'); assert.equal(await r.text(), '2345');
  r = await fetch(x.app.origin + '/media.dat', { headers: { Range: 'bytes=-3' } }); assert.equal(await r.text(), '789');
  r = await fetch(x.app.origin + '/media.dat', { headers: { Range: 'bytes=99-' } }); assert.equal(r.status, 416);
});
