#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { args, write } = require('./lib');
function rgb(hex) {
  if (!/^#(?:[\da-f]{3}|[\da-f]{6})$/i.test(hex)) throw new Error('Color must be #RGB or #RRGGBB');
  let h = hex.slice(1); if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
}
function hex(values) { return '#' + values.map(v => Math.round(v).toString(16).padStart(2, '0')).join(''); }
function luminance(color) {
  const c = rgb(color).map(v => v / 255).map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return c[0] * 0.2126 + c[1] * 0.7152 + c[2] * 0.0722;
}
function contrast(a, b) { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
function readable(color, background) {
  rgb(color);
  if (contrast(color, background) >= 4.5) return hex(rgb(color));
  const target = luminance(background) > 0.3 ? 0 : 255;
  for (let n = 1; n <= 100; n++) {
    const adjusted = hex(rgb(color).map(v => v * (1 - n / 100) + target * n / 100));
    if (contrast(adjusted, background) >= 4.5) return adjusted;
  }
  throw new Error('Unable to produce readable color');
}
function main(argv = process.argv.slice(2)) {
  const o = args(argv, ['primary', 'mode', 'font-pairing', 'output'], ['force', 'help']);
  if (o.help) { console.log('node generate-theme.js --output styles.css [--primary "#24577a"] [--mode light|dark] [--font-pairing modern|academic|mono-heavy] [--force]'); return; }
  const mode = o.mode || 'light'; if (!['light', 'dark'].includes(mode)) throw new Error('Mode must be light or dark');
  const pairing = o['font-pairing'] || 'modern'; if (!['modern', 'academic', 'mono-heavy'].includes(pairing)) throw new Error('Unknown font pairing');
  const bg = mode === 'dark' ? '#17232f' : '#fafbfc';
  const fg = mode === 'dark' ? '#f0f4f7' : '#172b3a';
  const muted = mode === 'dark' ? '#bac7d0' : '#4a5c6b';
  const primary = readable(o.primary || '#24577a', bg);
  const box = mode === 'dark' ? '#223443' : '#eef2f5';
  const normal = 'system-ui,"Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif';
  const heading = pairing === 'academic' ? 'Georgia,"Noto Serif CJK SC","Songti SC",serif' : pairing === 'mono-heavy' ? `ui-monospace,${normal}` : normal;
  const root = `:root {
  --background-color:${bg}; --text-color:${fg}; --muted-color:${muted};
  --color-primary:${primary}; --primary-color:var(--color-primary);
  --color-secondary:${readable('#356b61', bg)}; --secondary-color:var(--color-secondary); --color-accent:${readable('#8c4436', bg)};
  --box-bg:${box}; --box-border:${mode === 'dark' ? '#648399' : '#bcc9d2'};
  --callout-bg:${box}; --callout-border:var(--color-primary); --stat-card-bg:var(--box-bg); --feature-card-bg:var(--box-bg); --code-bg:#1d2430;
  --heading-font:${heading}; --body-font:${normal};
  --text-size:21pt; --h1-size:43pt; --h2-size:31pt; --h3-size:25pt; --footnote-size:12pt;
  --slide-padding:52px; --slide-padding-top:34px; --content-gap:20px; --box-radius:8px;
}`;
  const checks = [['text', fg, bg], ['muted', muted, bg], ['primary', primary, bg], ['callout', fg, box]];
  if (checks.some(([, a, b]) => contrast(a, b) < 4.5)) throw new Error('Theme contrast failed');
  const base = fs.readFileSync(path.join(__dirname, '../references/base-styles.css'), 'utf8');
  write(o.output || 'styles.css', base.replace(/:root\s*\{[^}]*\}/, root), o.force);
  console.log(JSON.stringify({ mode, primary, checks: checks.map(([role, a, b]) => ({ role, contrast: contrast(a, b), passed: true })) }));
}
if (require.main === module) { try { main(); } catch (e) { console.error(e.message); process.exitCode = 1; } }
module.exports = { main, contrast, readable };
