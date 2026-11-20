#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { args, integer, escape, write, digest } = require('./lib');
const { prepare } = require('./prepare-assets');
function structure(value) {
  return value.split(',').map(s => s === 'd' ? 'd' : integer(s, 'Structure', 1, 100));
}
function main(argv = process.argv.slice(2)) {
  const o = args(argv, ['slides', 'structure', 'output', 'title', 'styles', 'features', 'plan', 'lang'], ['help', 'force']);
  if (o.help) { console.log('node create-presentation.js --output talk.html [--plan talk-plan.json | --slides N | --structure 1,d,2] [--features charts,math,code,mermaid] [--force]'); return; }
  if ([o.plan, o.slides, o.structure].filter(x => x !== undefined).length > 1) throw new Error('Choose one of --plan, --slides, --structure');
  const dest = path.resolve(o.output || 'presentation.html');
  if (fs.existsSync(dest) && !o.force) throw new Error('Output exists; choose a new path or --force (creates backup)');
  const style = o.styles || 'styles.css';
  if (path.basename(style) !== style || !style.endsWith('.css')) throw new Error('--styles must be a local CSS filename');
  let plan = null;
  if (o.plan) { plan = JSON.parse(fs.readFileSync(o.plan, 'utf8')); if (!Array.isArray(plan.slides) || !plan.slides.length) throw new Error('Plan needs nonempty slides'); }
  const features = (o.features || '').split(',').filter(Boolean);
  for (const f of features) if (!['charts', 'math', 'code', 'mermaid'].includes(f)) throw new Error(`Unsupported feature: ${f}`);
  const groups = plan ? plan.slides.map(s => [s]) : (o.structure ? structure(o.structure) : Array(integer(o.slides || 5, 'slides')).fill(1)).map((n, h) =>
    n === 'd' ? [{ id: `section-${h + 1}`, title: '章节标题', role: 'divider' }] : Array.from({ length: n }, (_, v) => ({ id: n === 1 ? `slide-${h + 1}` : `slide-${h + 1}-${v + 1}`, title: h === 0 ? (o.title || '汇报标题') : '本页要回答的问题' })));
  const ids = new Set();
  for (const s of groups.flat()) {
    if (!/^[A-Za-z][\w-]*$/.test(s.id) || ids.has(s.id)) throw new Error('Slide IDs must be unique, starting with a letter');
    ids.add(s.id);
  }
  const asset = prepare(path.dirname(dest), features);
  const cssFile = path.join(path.dirname(dest), style);
  if (!fs.existsSync(cssFile)) write(cssFile, fs.readFileSync(path.join(__dirname, '../references/base-styles.css')));
  const slides = groups.map(group => {
    const html = group.map(s => `<section id="${escape(s.id)}"${s.role === 'divider' ? ' class="section-divider"' : ''}>
  <h2>${escape(s.title)}</h2>
  <div class="content" data-placeholder="content">
    <div class="visual-slot" data-placeholder="visual">需要落实的视觉表达：${escape(s.visual?.purpose || '按本页信息选择图片、图表、示意图或其他表达')}</div>
    <p>${escape(s.message || '根据真实材料补充本页主要信息；不得将此占位交付。')}</p>
  </div>
  <aside class="notes">${escape(s.notes || '补充解释顺序、条件、过渡和预计时间。')}</aside>
</section>`).join('\n');
    return group.length > 1 ? `<section>\n${html}\n</section>` : html;
  }).join('\n');
  const head = [`<link rel="stylesheet" href="${asset.base}/reveal/dist/reset.css">`, `<link rel="stylesheet" href="${asset.base}/reveal/dist/reveal.css">`, `<link rel="stylesheet" href="${escape(style)}">`];
  const scripts = [`<script src="${asset.base}/reveal/dist/reveal.js"></script>`, `<script src="${asset.base}/reveal/dist/plugin/notes.js"></script>`];
  if (features.includes('code')) { head.push(`<link rel="stylesheet" href="${asset.base}/reveal/dist/plugin/highlight/monokai.css">`); scripts.push(`<script src="${asset.base}/reveal/dist/plugin/highlight.js"></script>`); }
  if (features.includes('charts')) scripts.push(`<script src="${asset.base}/chart/chart.umd.js"></script>`);
  if (features.includes('math')) { head.push(`<link rel="stylesheet" href="${asset.base}/katex/katex.min.css">`); scripts.push(`<script src="${asset.base}/katex/katex.min.js"></script>`, `<script src="${asset.base}/katex/contrib/auto-render.min.js"></script>`); }
  if (features.includes('mermaid')) scripts.push(`<script src="${asset.base}/mermaid/mermaid.min.js"></script>`);
  scripts.push(`<script src="${asset.base}/runtime.js"></script>`);
  const html = `<!doctype html>\n<html lang="${escape(o.lang || 'zh-CN')}"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${escape(o.title || plan?.title || '科研汇报')}</title>\n${head.join('\n')}\n</head><body><div class="reveal"><div class="slides">\n${slides}\n</div></div>\n${scripts.join('\n')}\n<script>Presentation.start({ plugins: [RevealNotes${features.includes('code') ? ', RevealHighlight' : ''}] });</script>\n</body></html>\n`;
  write(dest, html, o.force);
  if (plan) {
    const copy = path.join(path.dirname(dest), `${path.basename(dest, path.extname(dest))}.plan.json`);
    if (path.resolve(o.plan) !== copy) write(copy, JSON.stringify(plan, null, 2) + '\n', o.force);
  }
  console.log(JSON.stringify({ html: dest, slides: ids.size, assets: asset.base, manifest_sha256: digest(JSON.stringify(asset.manifest)), placeholders: true }));
}
if (require.main === module) { try { main(); } catch (e) { console.error(e.message); process.exitCode = 1; } }
module.exports = { main, structure };
