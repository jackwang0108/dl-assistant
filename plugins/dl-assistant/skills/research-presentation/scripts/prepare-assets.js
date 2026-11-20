'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { digest } = require('./lib');
function packageRoot(name) {
  let p = path.dirname(require.resolve(name));
  while (p !== path.dirname(p)) {
    const f = path.join(p, 'package.json');
    if (fs.existsSync(f) && JSON.parse(fs.readFileSync(f)).name === name) return p;
    p = path.dirname(p);
  }
  throw new Error(`Install locked dependencies with npm ci: missing ${name}`);
}
function prepare(output, features = []) {
  const names = ['reveal.js', ...(features.includes('charts') ? ['chart.js'] : []), ...(features.includes('math') ? ['katex'] : []), ...(features.includes('mermaid') ? ['mermaid'] : [])];
  const roots = Object.fromEntries(names.map(n => [n, packageRoot(n)]));
  const versions = Object.fromEntries(names.map(n => [n, JSON.parse(fs.readFileSync(path.join(roots[n], 'package.json'))).version]));
  const runtime = path.join(__dirname, '../assets/runtime.js');
  const base = `vendor/research-presentation-${digest(JSON.stringify(versions) + fs.readFileSync(runtime) + fs.readFileSync(__filename)).slice(0, 12)}`;
  const manifest = { versions, files: {} };
  function copy(src, relative) {
    const stat = fs.lstatSync(src);
    if (stat.isDirectory()) { for (const name of fs.readdirSync(src)) copy(path.join(src, name), `${relative}/${name}`); return; }
    if (!stat.isFile()) throw new Error('Only regular dependency files can be bundled');
    const data = fs.readFileSync(src); const dest = path.join(output, base, relative);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    if (fs.existsSync(dest)) {
      if (!fs.lstatSync(dest).isFile() || digest(fs.readFileSync(dest)) !== digest(data)) throw new Error('Existing vendor file differs; use a new output directory');
    } else fs.writeFileSync(dest, data, { flag: 'wx' });
    manifest.files[relative] = digest(data);
  }
  for (const file of ['reset.css', 'reveal.css', 'reveal.js', 'plugin/notes.js']) copy(path.join(roots['reveal.js'], 'dist', file), `reveal/dist/${file}`);
  if (features.includes('code')) for (const file of ['plugin/highlight.js', 'plugin/highlight/monokai.css']) copy(path.join(roots['reveal.js'], 'dist', file), `reveal/dist/${file}`);
  if (features.includes('charts')) copy(path.join(roots['chart.js'], 'dist/chart.umd.js'), 'chart/chart.umd.js');
  if (features.includes('math')) {
    for (const file of ['katex.min.css', 'katex.min.js', 'contrib/auto-render.min.js', 'fonts']) copy(path.join(roots.katex, 'dist', file), `katex/${file}`);
  }
  if (features.includes('mermaid')) copy(path.join(roots.mermaid, 'dist/mermaid.min.js'), 'mermaid/mermaid.min.js');
  for (const [n, root] of Object.entries(roots)) {
    for (const f of ['LICENSE', 'LICENSE.md', 'LICENSE.txt']) if (fs.existsSync(path.join(root, f))) copy(path.join(root, f), `licenses/${n.replaceAll('.', '-')}-${f}`);
  }
  copy(runtime, 'runtime.js');
  const record = path.join(output, base, 'manifest.json');
  const bytes = JSON.stringify(manifest, null, 2) + '\n';
  if (fs.existsSync(record) && fs.readFileSync(record, 'utf8') !== bytes) throw new Error('Vendor manifest differs');
  if (!fs.existsSync(record)) fs.writeFileSync(record, bytes, { flag: 'wx' });
  return { base, manifest };
}
module.exports = { prepare, packageRoot };
